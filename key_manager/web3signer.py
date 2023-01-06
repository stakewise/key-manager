import urllib.parse

import click
import requests
from eth_typing import HexStr
from eth_utils import to_checksum_address


class Web3signer:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def upload_keys(self, keystores: list[str], passwords=list[str]):
        r = requests.post(
            url=urllib.parse.urljoin(self.endpoint, '/eth/v1/keystores'),
            json={
                'keystores': keystores,
                'passwords': passwords,
            },
        )

        if r.status_code != 200:
            raise click.ClickException(f'Web3signer connection error: {r.status_code} "{r.text}"')

    def list_keys(self) -> list[HexStr]:
        r = requests.get(url=urllib.parse.urljoin(self.endpoint, '/eth/v1/keystores'))

        if r.status_code != 200:
            raise click.ClickException(f'Web3signer connection error: {r.status_code} "{r.text}"')
        return [to_checksum_address(item.get('validating_pubkey')) for item in r.json().get('data')]

    def delete_keys(self, public_keys: list[HexStr]):
        r = requests.post(
            url=urllib.parse.urljoin(self.endpoint, '/eth/v1/keystores'),
            json={
                'pubkeys': [key.lower() for key in public_keys],
            },
        )

        if r.status_code != 200:
            raise click.ClickException(f'Web3signer connection error: {r.status_code} "{r.text}"')
