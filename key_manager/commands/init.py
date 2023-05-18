import click
from eth_typing import HexAddress

from key_manager.config import Config
from key_manager.credentials import CredentialManager
from key_manager.language import LANGUAGES, create_new_mnemonic
from key_manager.settings import AVAILABLE_NETWORKS, GOERLI
from key_manager.validators import validate_eth_address


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
    '--language',
    default='english',
    prompt='Choose your mnemonic language.',
    type=click.Choice(
        LANGUAGES,
        case_sensitive=False,
    ),
)
@click.option(
    '--vault',
    prompt='Enter your vault address',
    help='Vault address',
    type=str,
    callback=validate_eth_address,
)
@click.option(
    '--no-verify',
    is_flag=True,
    help='Skips mnemonic verification when provided.',
)
@click.command(help='Creates the mnemonic used to derive validator keys.')
def init(
    language: str,
    no_verify: bool,
    vault: HexAddress,
    network: str,
) -> None:
    if not language:
        language = click.prompt(
            'Choose your mnemonic language',
            default='english',
            type=click.Choice(LANGUAGES, case_sensitive=False),
        )
    mnemonic = create_new_mnemonic(language, skip_test=no_verify)

    first_public_key = _get_first_public_key(network, vault, str(mnemonic))

    config = Config(
        vault=vault,
        network=network,
        mnemonic_next_index=0,
        first_public_key=first_public_key
    )
    config.save()


def _get_first_public_key(network: str, vault: HexAddress, mnemonic: str) -> str:
    credentials = CredentialManager.generate_credentials(
        network=network,
        vault=vault,
        mnemonic=mnemonic,
        count=1,
        start_index=0,
    )

    return credentials[0].public_key
