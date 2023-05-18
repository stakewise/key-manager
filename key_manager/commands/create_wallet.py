import json
import time
from os import path
from pathlib import Path

import click
from eth_account import Account

from key_manager.contrib import greenify
from key_manager.password import get_or_create_password_file
from key_manager.settings import CONFIG_DIR
from key_manager.validators import validate_mnemonic


@click.option(
    '--mnemonic',
    help='The mnemonic for generating the wallet.',
    prompt='Enter the mnemonic for generating the wallet',
    type=str,
    callback=validate_mnemonic,
)
@click.command(help='Creates the encrypted hot wallet from the mnemonic.')
def create_wallet(mnemonic: str, wallet_dir: str) -> None:
    wallet_dir_path = Path(f'{CONFIG_DIR}/wallet')
    wallet_dir_path.mkdir(parents=True, exist_ok=True)
    wallet = _generate_encrypted_wallet(mnemonic, str(wallet_dir))
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
