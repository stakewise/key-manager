import json

import click
from eth_typing import HexStr
from sw_utils import get_consensus_client
from sw_utils.consensus import EXITED_STATUSES

from key_manager.consensus import get_validators
from key_manager.contrib import async_command
from key_manager.web3signer import Web3signer


@click.option(
    '--deposit-data-file',
    help='The current vault deposit data file. Defaults to ./data/deposit_data.json',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default='./data/deposit_data.json',
)
@click.option(
    '--consensus-endpoint',
    help='The endpoint of the consensus node.',
    prompt='Enter the endpoint of the consensus node',
    type=str,
)
@click.option(
    '--web3signer-endpoint',
    help='The endpoint of the web3signer service.',
    prompt='Enter the endpoint of the web3signer service',
    type=str,
)
@click.option(
    '--no-confirm',
    is_flag=True,
    default=False,
    help='Skips web3signer clean-up confirmation message when provided.',
)
@click.command(help='Removes the exited validator keys from the web3signer.')
@async_command
async def cleanup_keys(
    deposit_data_file: str,
    consensus_endpoint: str,
    web3signer_endpoint: str,
    no_confirm: bool,
) -> None:
    consensus_client = get_consensus_client(consensus_endpoint)

    web3signer = Web3signer(web3signer_endpoint)

    with open(deposit_data_file, 'r', encoding='utf-8') as f:
        deposit_data = json.load(f)

    deposit_data_keys = [data['pubkey'] for data in deposit_data]
    removed_keys = []

    current_keys = web3signer.list_keys()
    if not current_keys:
        raise click.ClickException('Web3signer does not contain any keys')

    with click.progressbar(
        length=len(current_keys),
        label='Checking validator keys:\t\t',
        show_percent=False,
        show_pos=True,
    ) as bar:

        index = 0
        total_count = len(current_keys)
        while index < total_count:
            chunk_size = min(100, total_count - index)

            public_keys_chunk: list[HexStr] = []
            while len(public_keys_chunk) != chunk_size:
                public_keys_chunk.append(current_keys[index])
                index += 1
            result = await get_validators(consensus_client, public_keys_chunk)
            registered_validators = {item['validator']['pubkey']: item['status'] for item in result}

            for public_key in public_keys_chunk:
                if public_key not in registered_validators and public_key not in deposit_data_keys:
                    removed_keys.append(public_key)

                if (
                    public_key in registered_validators
                    and registered_validators[public_key] in EXITED_STATUSES
                ):
                    removed_keys.append(public_key)

            bar.update(total_count - index)

    if not removed_keys:
        click.clear()
        click.secho(
            'Done. Unused keys not found.\n',
            bold=True,
            fg='green',
        )

    if not no_confirm:
        click.confirm(
            f'Found {len(removed_keys)} unused keys, remove them from the Web3Signer?',
            default=True,
            abort=True,
        )
    web3signer.delete_keys(removed_keys)

    click.clear()
    click.secho(
        f'Done. Deleted {len(removed_keys)} unused keys from {web3signer_endpoint}.',
        bold=True,
        fg='green',
    )
