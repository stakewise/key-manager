import json
from multiprocessing import Pool
from os import makedirs, path
from pathlib import Path

import click
from eth_typing import HexAddress

from key_manager.config import Config
from key_manager.contrib import async_command, greenify
from key_manager.credentials import Credential, CredentialManager
from key_manager.password import get_or_create_password_file
from key_manager.settings import CONFIG_DIR
from key_manager.validators import validate_eth_address, validate_mnemonic


@click.option(
    '--mnemonic',
    help='The mnemonic for generating the validator keys.',
    prompt='Enter the mnemonic for generating the validator keys',
    type=str,
    callback=validate_mnemonic,
)
@click.option(
    '--count',
    help='The number of the validator keys to generate.',
    prompt='Enter the number of the validator keys to generate',
    type=click.IntRange(min=1),
)
@click.option(
    '--vault',
    '--withdrawal-address',
    help='The withdrawal address where the funds will be sent after validators withdrawals.',
    prompt='Enter the Vault address',
    type=str,
    callback=validate_eth_address,
)
@click.command(help='Creates the validator keys from the mnemonic.')
@async_command
async def create_keys(
    mnemonic: str,
    count: int,
    vault: HexAddress,
) -> None:
    vault_dir = Path(CONFIG_DIR) / str(vault)
    config_path = vault_dir / 'config'
    deposit_data_file = vault_dir / 'deposit_data.json'
    keystores_dir = vault_dir / 'keystores'
    password_file = keystores_dir / 'password.txt'

    config = Config(vault=vault)
    config.load()

    credentials = CredentialManager.generate_credentials(
        network=str(config.network),
        vault=vault,
        mnemonic=mnemonic,
        count=count,
        start_index=config.mnemonic_next_index,
    )
    deposit_data = _export_deposit_data_json(
        credentials=credentials,
        filename=str(deposit_data_file)
    )

    _export_keystores(
        credentials=credentials,
        keystores_dir=str(keystores_dir),
        password_file=str(password_file)
    )

    config.update(mnemonic_next_index=config.mnemonic_next_index+count)

    click.echo(
        f'Done. Generated {greenify(count)} keys for {greenify(vault)} vault.\n'
        f'Keystores saved to {greenify(keystores_dir)} file\n'
        f'Deposit data saved to {greenify(deposit_data)} file\n'
        f'Next mnemonic start index saved to {config_path} file',
    )


def _export_deposit_data_json(credentials: list[Credential], filename: str) -> str:
    with click.progressbar(
        length=len(credentials),
        label='Generating deposit data JSON\t\t',
        show_percent=False,
        show_pos=True,
    ) as bar, Pool() as pool:
        results = [
            pool.apply_async(
                cred.deposit_datum_dict,
                callback=lambda x: bar.update(1),
            )
            for cred in credentials
        ]
        for result in results:
            result.wait()
        deposit_data = [result.get() for result in results]

    makedirs(path.dirname(path.abspath(filename)), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(deposit_data, f, default=lambda x: x.hex())
    return filename


def _export_keystores(
    credentials: list[Credential], keystores_dir: str, password_file: str
) -> None:
    makedirs(path.abspath(keystores_dir), exist_ok=True)
    password = get_or_create_password_file(password_file)
    with click.progressbar(
        credentials,
        label='Exporting validator keystores\t\t',
        show_percent=False,
        show_pos=True,
    ) as bar, Pool() as pool:
        results = [
            pool.apply_async(
                cred.save_signing_keystore,
                kwds=dict(password=password, folder=keystores_dir),
                callback=lambda x: bar.update(1),
            )
            for cred in credentials
        ]

        for result in results:
            result.wait()
