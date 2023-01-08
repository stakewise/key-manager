import click
from eth_typing import HexStr
from sw_utils import get_consensus_client, get_execution_client
from sw_utils.consensus import EXITED_STATUSES

from key_manager.consensus import get_validators
from key_manager.contrib import async_command
from key_manager.execution import VaultContract, get_current_number
from key_manager.ipfs import fetch_vault_deposit_data
from key_manager.settings import AVAILABLE_NETWORKS, IPFS_ENDPOINTS, MAINNET, NETWORKS
from key_manager.validators import validate_eth_address
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
    '--web3signer-endpoint',
    help='The endpoint of the web3signer service.',
    prompt='Enter the endpoint of the web3signer service',
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
    '--no-confirm',
    is_flag=True,
    default=False,
    help='Skips web3signer clean-up confirmation message when provided.',
)
@click.command(help='Removes the exited validator keys from the web3signer')
@async_command
async def cleanup_keys(
    network: str,
    vault: str,
    execution_endpoint: str,
    consensus_endpoint: str,
    ipfs_endpoints: list[str],
    web3signer_endpoint: str,
    no_confirm: bool,
) -> None:
    execution_client = get_execution_client(execution_endpoint, is_poa=NETWORKS[network].IS_POA)
    consensus_client = get_consensus_client(consensus_endpoint)

    web3signer = Web3signer(web3signer_endpoint)
    current_block = await get_current_number(execution_client=execution_client)

    deposit_data_keys = []
    removed_keys = []
    current_validator_ipfs_hash = await VaultContract(
        address=vault,
        execution_client=execution_client,
        genesis_block=NETWORKS[network].VAULT_CONTRACT_GENESIS_BLOCK,
    ).get_last_validators_root_updated_event(current_block)

    if current_validator_ipfs_hash:
        deposit_data_keys = await fetch_vault_deposit_data(
            ipfs_endpoints, current_validator_ipfs_hash
        )

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
