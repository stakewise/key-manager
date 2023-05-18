import json
import time
from os import path

import click
from eth_account import Account

from key_manager.contrib import greenify
from key_manager.password import get_or_create_password_file
from key_manager.settings import CONFIG_DIR
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
    if not wallet_dir:
        wallet_dir = f'{CONFIG_DIR}/wallet'
    wallet = _generate_encrypted_wallet(mnemonic, wallet_dir)
    click.echo(f'Done. Wallet {greenify(wallet)} saved to {greenify(wallet_dir)} directory')


def _generate_encrypted_wallet(mnemonic: str, wallet_dir: str) -> str:
    Account.enable_unaudited_hdwallet_features()

    account = Account().from_mnemonic(mnemonic=mnemonic)
    password = get_or_create_password_file(path.join(wallet_dir, 'password.txt'))
    encrypted_data = Account.encrypt(account.key, password=password)

    wallet_name = f'{account.address}-{int(time.time())}.json'
    with open(path.join(wallet_dir, wallet_name), 'w', encoding='utf-8') as f:
        json.dump(encrypted_data, f, default=lambda x: x.hex())

    return wallet_name
