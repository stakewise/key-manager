import json
import tempfile
from pathlib import Path

import click
from eth_typing import HexAddress

from key_manager.commands.create_keys import export_keystores
from key_manager.credentials import CredentialManager
from key_manager.language import LANGUAGES, create_new_mnemonic
from key_manager.settings import AVAILABLE_NETWORKS, CONFIG_DIR, GOERLI
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
    vault_dir = Path(CONFIG_DIR) / vault
    try:
        vault_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as e:
        raise click.ClickException(f'{e}')

    if not language:
        language = click.prompt(
            'Choose your mnemonic language',
            default='english',
            type=click.Choice(LANGUAGES, case_sensitive=False),
        )
    mnemonic = create_new_mnemonic(language, skip_test=no_verify)

    first_public_key = _get_first_public_key(network, vault, str(mnemonic))

    config = {
        'network': network,
        'mnemonic_next_index': 0,
        'first_public_key': first_public_key
    }
    try:
        with (vault_dir / 'config').open('w') as f:
            json.dump(config, f)
    except FileNotFoundError as e:
        raise click.ClickException(str(e))

    click.secho(f'Configuration saved in {vault_dir}/config', bold=True, fg='green')


def _get_first_public_key(network: str, vault: HexAddress, mnemonic: str) -> str:
    credentials = CredentialManager.generate_credentials(
        network=network,
        vault=vault,
        mnemonic=mnemonic,
        count=1,
        start_index=0,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        CONFIG_DIR = Path(temp_dir)
        keystores_dir = CONFIG_DIR / 'keystores'
        password_file = keystores_dir / 'password.txt'
        export_keystores(
            credentials=credentials,
            keystores_dir=str(keystores_dir),
            password_file=str(password_file)
        )
        keystore_files = sorted(
            keystores_dir.glob('keystore-*'),
            key=lambda path: path.stat().st_ctime
        )
        try:
            with keystore_files[0].open('r') as f:
                data = json.load(f)
                first_public_key = data.get('pubkey')
                return first_public_key
        except FileNotFoundError as e:
            raise click.ClickException(str(e))
