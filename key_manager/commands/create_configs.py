import click


@click.option(
    '--fee-recipient',
    required=True,
    help='The recipient address for MEV & priority fees.',
    prompt='Enter the recipient address for MEV & priority fees.',
    type=str,
)
@click.option(
    '--total-validators',
    required=True,
    help='The total number of validators connected to the web3signer.',
    prompt='Enter the total number of validators connected to the web3signer.',
    type=int,
)
@click.option(
    '--validator-index',
    required=True,
    help='The validator index to generate the configuration files. '
         'Must be less than total-validators.',
    prompt='Enter the validator index to generate the configuration files. '
           'Must be less than total-validators.',
    type=int,
)
@click.option(
    '--web3signer-endpoint',
    required=False,
    help='The endpoint of the execution node.',
    prompt='Enter the endpoint of the execution node.',
    type=str,
)
@click.option(
    '--output-dir',
    help='The directory to store randomly generated password for encrypting the keystores. '
         'It is ignored when web3signer-endpoint is used. '
         'Defaults to ./<keystores-dir>/password.txt.',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    '--disable-proposal-builder',
    is_flag=True,
    help='Disable proposal builder for Teku and Prysm clients',
)
@click.command(
    help='Creates validator configuration files for Lighthouse, '
         'Prysm, and Teku clients to sign data using web3signer.'
)
# pylint: disable-next=unused-argument
def create_configs(
    fee_recipient: str,
    total_validators: int,
    validator_index: int,
    web3signer_endpoint: str,
    output_dir: str,
    disable_proposal_builder: bool,
) -> None:
    ...
