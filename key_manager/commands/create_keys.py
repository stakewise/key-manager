import click
from eth_typing import BlockNumber, HexAddress
from sw_utils import get_execution_client

from key_manager.contrib import async_command
from key_manager.credentials import (
    export_deposit_data_json,
    export_keystores,
    generate_credentials,
)
from key_manager.execution import (
    ValidatorRegistryContract,
    VaultContract,
    get_current_number,
)
from key_manager.ipfs import fetch_vault_deposit_data
from key_manager.password import generate_password
from key_manager.settings import AVAILABLE_NETWORKS, IPFS_ENDPOINTS, MAINNET, NETWORKS
from key_manager.validators import validate_eth_address, validate_mnemonic
from key_manager.web3signer import Web3signer


@click.option(
    '--network',
    default=MAINNET,
    help='The network to generate the deposit data for',
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
    type=click.IntRange(min=1, max=10000),
)
@click.option(
    '--vault',
    help='The vault address for which the validator keys are generated.',
    prompt='Enter the vault address for which the validator keys are generated',
    type=str,
    callback=validate_eth_address,
)
@click.option(
    '--execution-endpoint',
    help='The endpoint of the execution node.',
    prompt='Enter the endpoint of the execution node',
    type=str,
)
@click.option(
    '--consensus-endpoint',
    help='The endpoint of the consensus node.',
    prompt='Enter the endpoint of the consensus node',
    type=str,
)
@click.option(
    '--ipfs-endpoints',
    required=False,
    help='The IPFS endpoints.',
    default=IPFS_ENDPOINTS,
    type=str,
)
@click.option(
    '--deposit-data-file',
    help='The file to store the deposit data file. Defaults to ./data/deposit_data.json',
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
    default='./data/deposit_data.json',
)
@click.option(
    '--keystores-dir',
    required=False,
    help='The directory to store the validator keys in the EIP-2335 standard.'
    ' It is ignored when web3signer-endpoint is used. Defaults to ./data/keystores.',
    default='./data/keystore',
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
)
@click.option(
    '--password-file',
    required=False,
    help='The file to store randomly generated password for encrypting the keystores. '
    'It is ignored when web3signer-endpoint is used. '
    'Defaults to ./<keystores-dir>/password.txt.',
    default='./data/keystore/password.txt',
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
)
@click.option(
    '--web3signer-endpoint',
    required=False,
    help='The endpoint of the web3signer service.',
    type=str,
)
@click.option(
    '--no-confirm',
    is_flag=True,
    default=False,
    help='Skips web3signer upload confirmation message when provided.',
)
@click.command(help='Creates the validator keys from the mnemonic.')
@async_command
async def create_keys(
    network: str,
    mnemonic: str,
    count: int,
    vault: HexAddress,
    execution_endpoint: str,
    consensus_endpoint: str,
    ipfs_endpoints: list[str],
    deposit_data_file: str,
    keystores_dir: str,
    password_file: str,
    web3signer_endpoint: str,
    no_confirm: bool,
) -> None:
    execution_client = get_execution_client(execution_endpoint, is_poa=NETWORKS[network].IS_POA)

    current_block = await get_current_number(execution_client=execution_client)
    fetch_from_block = BlockNumber(current_block - NETWORKS[network].BEACON_SYNC_BLOCK_DISTANCE)

    used_keys = []
    current_validator_ipfs_hash = await VaultContract(
        address=vault,
        execution_client=execution_client,
        genesis_block=NETWORKS[network].VAULT_CONTRACT_GENESIS_BLOCK,
    ).get_last_validators_root_updated_event(current_block)

    if current_validator_ipfs_hash:
        current_keys = await fetch_vault_deposit_data(ipfs_endpoints, current_validator_ipfs_hash)
        used_keys.extend(current_keys)

    network_validators_keys = await ValidatorRegistryContract(
        address=NETWORKS[network].VALIDATORS_REGISTRY_CONTRACT_ADDRESS,
        execution_client=execution_client,
        genesis_block=NETWORKS[network].VALIDATORS_REGISTRY_GENESIS_BLOCK,
    ).get_latest_network_validator_public_keys(from_block=fetch_from_block, to_block=current_block)
    used_keys.extend(network_validators_keys)

    credentials = await generate_credentials(
        network=network,
        vault=vault,
        mnemonic=mnemonic,
        count=count,
        used_keys=used_keys,
        consensus_endpoint=consensus_endpoint,
    )
    deposit_data = export_deposit_data_json(credentials=credentials, filename=deposit_data_file)

    if web3signer_endpoint:
        if not no_confirm:
            click.confirm(
                f'Generated {count} keystores, upload them to the Web3Signer?',
                default=True,
                abort=True,
            )

        keystores, passwords = [], []
        with click.progressbar(
            credentials,
            label='Generating keystores for web3signer\t\t',
            show_percent=False,
            show_pos=True,
        ) as _credentials:
            for credential in _credentials:
                password = generate_password()
                keystores.append(credential.signing_keystore(password).as_json())
                passwords.append(password)

        Web3signer(web3signer_endpoint).upload_keys(
            keystores=keystores,
            passwords=passwords,
        )

    else:
        export_keystores(
            credentials=credentials, keystores_dir=keystores_dir, password_file=password_file
        )

    click.clear()
    click.secho(
        f'Done. Generated {count} keys for {vault} vault.\n'
        f'Deposit data saved to {deposit_data} file',
        bold=True,
        fg='green',
    )
