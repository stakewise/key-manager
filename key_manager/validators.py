import os
import re

import click
from eth_utils import is_address, to_checksum_address


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
def validate_db_uri(ctx, param, value):
    pattern = re.compile(r'.+:\/\/.+:.*@.+\/.+')
    if not pattern.match(value):
        raise click.BadParameter('Invalid database connection string')
    return value


# pylint: disable-next=unused-argument
def validate_env_name(ctx, param, value):
    if not os.getenv(value):
        raise click.BadParameter(f'Empty environment variable {value}')
    return value
