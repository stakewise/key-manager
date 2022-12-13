import click

from key_manager.networks import AVAILABLE_NETWORKS, MAINNET


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
    required=True,
    help='The vault address for which the validator keys are generated.',
    prompt='Enter the vault address for which the validator keys are generated.',
    type=str,
)
@click.option(
    '--execution-endpoint',
    required=True,
    help='The endpoint of the execution node.',
    prompt='Enter the endpoint of the execution node.',
    type=str,
)
@click.option(
    '--web3signer-endpoint',
    required=False,
    help='The endpoint of the execution node.',
    prompt='Enter the endpoint of the execution node.',
    type=str,
)
@click.option(
    '--ipfs-endpoints',
    required=False,
    help='The endpoint of the execution node.',
    prompt='Enter the endpoint of the execution node.',
    default='фывфывфыв',
    type=str,
)
@click.option(
    '--no-confirm',
    is_flag=True,
    default=False,
    help='Skips web3signer clean-up confirmation message when provided.',
)
@click.command(help='Removes the exited validator keys from the web3signer')
# pylint: disable-next=unused-argument
def cleanup_keys(
    network: str,
    vault: str,
    execution_endpoint: str,
    ipfs_endpoints: list[str],
    web3signer_endpoint: str,
    no_confirm: bool,
) -> None:
    ...
