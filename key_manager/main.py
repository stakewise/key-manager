import multiprocessing

import click

from key_manager.commands.sync_validator import sync_validator
from key_manager.commands.sync_web3signer import sync_web3signer
from key_manager.commands.update_db import update_db


@click.group()
def cli() -> None:
    pass


cli.add_command(update_db)
cli.add_command(sync_web3signer)
cli.add_command(sync_validator)


if __name__ == '__main__':
    # Pyinstaller hacks
    multiprocessing.set_start_method('spawn')
    multiprocessing.freeze_support()

    cli()
