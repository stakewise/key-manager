import click

from key_manager.contrib import greenify
from key_manager.credentials import generate_encrypted_wallet
from key_manager.validators import validate_empty_dir, validate_mnemonic


@click.option(
    '--mnemonic',
    help='The mnemonic for generating the wallet.',
    prompt='Enter the mnemonic for generating the wallet',
    type=str,
    callback=validate_mnemonic,
)
@click.option(
    '--wallet-dir',
    required=False,
    help='The directory to save encrypted wallet and password files. Defaults to ./wallet.',
    default='./wallet',
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    callback=validate_empty_dir,
)
@click.command(help='Creates the encrypted hot wallet from the mnemonic.')
def create_wallet(mnemonic: str, wallet_dir: str) -> None:
    wallet = generate_encrypted_wallet(mnemonic, wallet_dir)
    click.echo(f'Done. Wallet {greenify(wallet)} saved to {greenify(wallet_dir)} directory')
