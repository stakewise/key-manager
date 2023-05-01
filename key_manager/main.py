import multiprocessing

import click

from key_manager.commands.create_keys import create_keys
from key_manager.commands.create_mnemonic import create_mnemonic
from key_manager.commands.create_wallet import create_wallet
from key_manager.commands.merge_deposit import merge_deposit
from key_manager.commands.sync_validator import sync_validator
from key_manager.commands.sync_web3signer import sync_web3signer
from key_manager.commands.update_db import update_db


@click.group()
def cli() -> None:
    pass


cli.add_command(create_mnemonic)
cli.add_command(create_keys)
cli.add_command(create_wallet)
cli.add_command(merge_deposit)
cli.add_command(update_db)
cli.add_command(sync_web3signer)
cli.add_command(sync_validator)


if __name__ == '__main__':
    # Pyinstaller hacks
    multiprocessing.set_start_method('spawn')
    multiprocessing.freeze_support()

    cli()
