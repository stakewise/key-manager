from pathlib import Path

import click
from eth_typing import HexAddress
from eth_utils import is_address, to_checksum_address
from sw_utils import get_execution_client

from key_manager.contrib import async_command, greenify
from key_manager.credentials import (
    export_deposit_data_json,
    export_keystores,
    generate_credentials,
)
from key_manager.execution import generate_vault_address
from key_manager.password import get_or_create_password_file
from key_manager.settings import AVAILABLE_NETWORKS, GOERLI, NETWORKS, VAULT_TYPE
from key_manager.validators import (
    validate_empty_dir,
    validate_eth_address,
    validate_mnemonic,
)
from key_manager.web3signer import Web3signer


@click.option(
    '--network',
    default=GOERLI,
    help='The network to generate the deposit data for.',
    prompt='Enter the network name',
    type=click.Choice(
        AVAILABLE_NETWORKS,
        case_sensitive=False,
    ),
)
@click.option(
    '--mnemonic',
    help='The mnemonic for generating the validator keys.',
    prompt='Enter the mnemonic for generating the validator keys',
    type=str,
    callback=validate_mnemonic,
)
@click.option(
    '--count',
    help='The number of the validator keys to generate.',
    prompt='Enter the number of the validator keys to generate',
    type=click.IntRange(min=1),
)
@click.option(
    '--vault',
    '--withdrawal-address',
    help='The withdrawal address where the funds will be sent after validators’ withdrawals.',
    type=str,
    callback=validate_eth_address,
    required=False,
)
@click.option(
    '--admin',
    help='The vault admin address.',
    type=str,
    required=False,
)
@click.option(
    '--vault-type',
    help='The vault type.',
    type=click.Choice(
        [opt.value for opt in VAULT_TYPE],
        case_sensitive=False,
    ),
    required=False,
    prompt=False,
)
@click.option(
    '--execution-endpoint',
    required=False,
    help='The endpoint of the execution node used for computing the withdrawal address.',
    type=str,
)
@click.option(
    '--deposit-data-file',
    help='The path to store the deposit data file. Defaults to ./data/deposit_data.json',
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
    default='./data/deposit_data.json',
)
@click.option(
    '--keystores',
    required=False,
    help='The directory to store the validator keys in the EIP-2335 standard.'
    ' Defaults to ./data/keystores.',
    default='./data/keystores',
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    callback=validate_empty_dir,
)
@click.option(
    '--password-file',
    required=False,
    help='The path to store randomly generated password for encrypting the keystores.'
    ' Defaults to ./data/keystores/password.txt.',
    default='./data/keystores/password.txt',
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
)
@click.option(
    '--web3signer-endpoint',
    required=False,
    help='The endpoint of the web3signer service for uploading the keystores.',
    type=str,
)
@click.option(
    '--mnemonic-start-index',
    required=False,
    help="The index of the first validator's keys you wish to generate."
    ' If this is your first time generating keys with this mnemonic, use 0.'
    ' If you have generated keys using this mnemonic before,'
    ' add --mnemonic-next-index-file flag or specify the next index from which you want'
    " to start generating keys from (eg, if you've generated 4 keys before (keys #0, #1, #2, #3),"
    ' then enter 4 here.',
    type=click.IntRange(min=0),
)
@click.option(
    '--mnemonic-next-index-file',
    help='The path where to store the mnemonic index to use for generating next validator keys.'
    ' Used to always generate unique validator keys.'
    ' Defaults to ./mnemonic_next_index.txt',
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
    default='./mnemonic_next_index.txt',
)
@click.option(
    '--no-confirm',
    is_flag=True,
    default=False,
    help='Skips confirmation messages when provided.',
)
@click.command(help='Creates the validator keys from the mnemonic.')
@async_command
async def create_keys(
    network: str,
    mnemonic: str,
    count: int,
    vault: HexAddress | None,
    admin: HexAddress | None,
    vault_type: str | None,
    execution_endpoint: str | None,
    deposit_data_file: str,
    keystores: str,
    password_file: str,
    web3signer_endpoint: str,
    mnemonic_start_index: int | None,
    mnemonic_next_index_file: str,
    no_confirm: bool,
) -> None:
    if not vault and admin and vault_type and execution_endpoint:
        execution_client = get_execution_client(execution_endpoint, is_poa=NETWORKS[network].IS_POA)
        vault = await generate_vault_address(
            admin=admin, vault_type=vault_type, execution_client=execution_client, network=network
        )
    elif not vault and (admin or vault_type or execution_endpoint):
        raise click.BadParameter(
            'You must provide either the withdrawal address'
            ' or execution endpoint, vault type, and admin address'
        )
    elif not vault:
        vault = click.prompt(
            'Enter the withdrawal address for which the validator keys are generated'
        )
        if not is_address(vault):
            raise click.BadParameter('Invalid Ethereum address')
        vault = to_checksum_address(vault)  # type: ignore

    if mnemonic_start_index is None:
        if not Path(mnemonic_next_index_file).is_file():
            mnemonic_start_index = click.prompt(
                'Enter the mnemonic start index for generating validator keys',
                type=click.IntRange(min=0),
                default=0,
            )
        else:
            with open(mnemonic_next_index_file, 'r', encoding='utf-8') as f:
                mnemonic_start_index = int(f.read())

    credentials = await generate_credentials(
        network=network,
        vault=vault,
        mnemonic=mnemonic,
        count=count,
        start_index=mnemonic_start_index,
    )
    deposit_data = export_deposit_data_json(credentials=credentials, filename=deposit_data_file)

    export_keystores(credentials=credentials, keystores_dir=keystores, password_file=password_file)

    with open(mnemonic_next_index_file, 'w', encoding='utf-8') as f:
        f.write(str(mnemonic_start_index + count))

    if web3signer_endpoint:
        if not no_confirm:
            click.confirm(
                f'Generated {count} keystores, upload them to the Web3Signer?',
                default=True,
                abort=True,
            )
        password = get_or_create_password_file(password_file)
        keys = []
        with click.progressbar(
            credentials,
            label='Uploading keystores to web3signer\t\t',
            show_percent=False,
            show_pos=True,
        ) as _credentials:
            for credential in _credentials:
                keys.append(credential.signing_keystore(password).as_json())

        Web3signer(web3signer_endpoint).upload_keys(
            keystores=keys,
            passwords=[password] * len(keys),
        )

    click.clear()

    click.echo(
        f'Done. Generated {greenify(count)} keys for {greenify(vault)} vault.\n'
        f'Keystores saved to {greenify(keystores)} file\n'
        f'Deposit data saved to {greenify(deposit_data)} file\n'
        f'Next mnemonic start index saved to {greenify(mnemonic_next_index_file)} file',
    )
