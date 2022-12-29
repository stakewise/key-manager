import click
from eth_utils import is_address, to_checksum_address

from key_manager.language import validate_mnemonic as verify_mnemonic


# pylint: disable-next=unused-argument
def validate_mnemonic(ctx, param, value):
    value = value.replace('"', '')
    return verify_mnemonic(value)


# pylint: disable-next=unused-argument
def validate_eth_address(ctx, param, value):
    try:
        if is_address(value):
            return to_checksum_address(value)
    except ValueError:
        pass

    raise click.BadParameter('Invalid Ethereum address')
