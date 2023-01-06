import urllib.parse

import click
import requests


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
