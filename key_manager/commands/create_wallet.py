import json
import time
from os import path
from pathlib import Path

import click
from eth_account import Account
from eth_typing import HexAddress

from key_manager.contrib import greenify
from key_manager.password import get_or_create_password_file
from key_manager.settings import CONFIG_DIR
from key_manager.validators import validate_eth_address, validate_mnemonic


@click.option(
    '--mnemonic',
    help='The mnemonic for generating the wallet.',
    prompt='Enter the mnemonic for generating the wallet',
    type=str,
    callback=validate_mnemonic,
)
@click.option(
    '--vault',
    '--withdrawal-address',
    help='The withdrawal address where the funds will be sent after validators withdrawals.',
    prompt='Enter the Vault address',
    type=str,
    callback=validate_eth_address,
)
@click.command(help='Creates the encrypted hot wallet from the mnemonic.')
def create_wallet(mnemonic: str, vault: HexAddress,) -> None:
    wallet_dir = Path(f'{CONFIG_DIR}/{vault}/wallet')
    wallet_dir.mkdir(parents=True, exist_ok=True)
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