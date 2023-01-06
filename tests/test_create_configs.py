import unittest
from unittest.mock import patch

from click.testing import CliRunner

from key_manager.commands.create_configs import create_configs

from .factories import faker


class TestCreateConfig(unittest.TestCase):
    def test_basic(self):
        fee_recipient = faker.eth_address()
        total_validators = 100
        validator_index = 51

        public_keys = [faker.eth_public_key() for x in range(1000)]

        runner = CliRunner()
        args = [
            '--fee-recipient',
            fee_recipient,
            '--total-validators',
            total_validators,
            '--validator-index',
            validator_index,
            '--web3signer-endpoint',
            'https://example.com',
        ]

        with runner.isolated_filesystem(), patch(
            'key_manager.commands.create_configs.Web3signer.list_keys',
            return_value=public_keys,
        ):
            result = runner.invoke(create_configs, args)

            assert result.exit_code == 0
            output = '''
Done. Generated configs with 10 keys for validator #51.
Validator definitions for Lighthouse saved to data/configs/validator_definitions.yml file.
Signer keys for Teku\\Prysm saved to data/configs/signer_keys.yml file.
Proposer config for Teku\\Prysm saved to data/configs/proposer_config.json file.
'''
            assert output.strip() == result.output.strip()
            validator_public_keys = public_keys[510:520]
            with open('./data/configs/validator_definitions.yml', encoding='utf-8') as f:
                s = """---"""
                for public_key in validator_public_keys:
                    s += f"""
- enabled: true
  suggested_fee_recipient: \'{fee_recipient}\'
  type: web3signer
  url: https://example.com
  voting_public_key: \'{public_key}\'"""
                s += '\n'
                assert f.read() == s

            with open('./data/configs/signer_keys.yml', encoding='utf-8') as f:
                # pylint: disable-next=line-too-long
                s = f"""validators-external-signer-public-keys: [{",".join('"' + x + '"' for x in validator_public_keys)}]"""
                ff = f.read()
                assert ff == s, (ff, s)

            with open('./data/configs/proposer_config.json', encoding='utf-8') as f:
                s = (
                    """{
    "default_config": {
        "fee_recipient": "%s",
        "builder": {
            "enabled": true
        }
    }
}"""
                    % fee_recipient
                )
                ff = f.read()

                assert ff == s, (ff, s)
