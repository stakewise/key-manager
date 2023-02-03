from pathlib import Path

import click
from eth_utils import is_address, to_checksum_address

from key_manager.language import validate_mnemonic as verify_mnemonic


# pylint: disable-next=unused-argument
def validate_mnemonic(ctx, param, value):
    value = value.replace('"', '')
    return verify_mnemonic(value)


# pylint: disable-next=unused-argument
def validate_eth_address(ctx, param, value):
    if not value:
        return None
    try:
        if is_address(value):
            return to_checksum_address(value)
    except ValueError:
        pass

    raise click.BadParameter('Invalid Ethereum address')


# pylint: disable-next=unused-argument
def validate_empty_dir(ctx, param, value):
    path = Path(value)
    if path.is_dir() and any(path.iterdir()):
        raise click.BadParameter(f'Keystores directory({value}) must be empty')
    return value
