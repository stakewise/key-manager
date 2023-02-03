import click

from key_manager.commands.cleanup_keys import cleanup_keys
from key_manager.commands.create_configs import create_configs
from key_manager.commands.create_keys import create_keys
from key_manager.commands.create_mnemonic import create_mnemonic
from key_manager.commands.create_wallet import create_wallet


@click.group()
def cli() -> None:
    pass


cli.add_command(create_mnemonic)
cli.add_command(create_keys)
cli.add_command(cleanup_keys)
cli.add_command(create_configs)
cli.add_command(create_wallet)

if __name__ == '__main__':
    cli()
