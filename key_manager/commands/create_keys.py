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
    '--count',
    required=True,
    help='The number of the validator keys to generate. Can be at most 10 000.',
    prompt='Enter the number of the validator keys to generate. Can be at most 10 000.',
    type=int,
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
    '--ipfs-endpoints',
    required=False,
    help='The endpoint of the execution node.',
    prompt='Enter the endpoint of the execution node.',
    default='фывфывфыв',
    type=str,
)
@click.option(
    '--deposit-data-dir',
    help='The directory to store the deposit data file',
    prompt='Enter the file path from where to read whitelisted accounts. One address per line',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    '--deposit-data-dir',
    help='The directory to store the deposit data file. Defaults to ./data/deposit_data',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    '--keystores-dir',
    help='The directory to store the validator keys in the EIP-2335 standard.'
         ' It is ignored when web3signer-endpoint is used. Defaults to ./data/keystores.',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    '--password-dir',
    help='The directory to store randomly generated password for encrypting the keystores. '
         'It is ignored when web3signer-endpoint is used. '
         'Defaults to ./<keystores-dir>/password.txt.',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    '--web3signer-endpoint',
    required=False,
    help='The endpoint of the execution node.',
    prompt='Enter the endpoint of the execution node.',
    type=str,
)
@click.option(
    '--no-confirm',
    is_flag=True,
    default=False,
    help='Skips mnemonic verification when provided.',
)
@click.command(help='Creates the validator keys from the mnemonic.')
# pylint: disable-next=unused-argument
def create_keys(
    network: str,
    count: int,
    vault: str,
    execution_endpoint: str,
    ipfs_endpoints: list[str],
    deposit_data_dir: str,
    keystores_dir: str,
    password_dir: str,
    web3signer_endpoint: str,
    no_confirm: bool,
) -> None:
    ...
