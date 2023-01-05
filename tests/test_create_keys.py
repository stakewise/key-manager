import json
import os
import random
import unittest
from unittest.mock import patch

from click.testing import CliRunner
from staking_deposit.key_handling.key_derivation.mnemonic import get_mnemonic

from key_manager import KEY_MANAGER_VERSION
from key_manager.commands.create_keys import create_keys
from key_manager.language import WORD_LISTS_PATH
from key_manager.settings import MAINNET

from .factories import faker

mnemonic = get_mnemonic(language='english', words_path=WORD_LISTS_PATH)


class TestCreateKeys(unittest.TestCase):
    def test_basic(self):
        vault = faker.eth_address()
        count = 5
        runner = CliRunner()
        args = [
            '--network',
            MAINNET,
            '--mnemonic',
            f'"{mnemonic}"',
            '--count',
            count,
            '--vault',
            vault,
            '--execution-endpoint',
            'https://example.com',
            '--consensus-endpoint',
            'https://example.com',
        ]
        with runner.isolated_filesystem(), patch(
            'key_manager.commands.create_keys.get_current_number',
            return_value=random.randint(10000, 1000000),
        ), patch(
            'key_manager.commands.create_keys.VaultContract.get_last_validators_root_updated_event',
            return_value=None,
        ), patch(
            'key_manager.commands.create_keys.ValidatorRegistryContract.'
            'get_latest_network_validator_public_keys',
            return_value=[],
        ), patch(
            'key_manager.credentials.ExtendedAsyncBeacon.get_validators_by_ids',
            return_value={'data': []},
        ):
            result = runner.invoke(create_keys, args)
            assert result.exit_code == 0

            output = f'''
            Creating validator keys:\t\t
Generating deposit data json\t\t
Exporting validator keystores\t\t
Done. Generated 5 keys for {vault} vault.
Deposit data saved to ./data/deposit_data.json file
'''
            assert output.strip() == result.output.strip()
            with open('./data/deposit_data.json', encoding='utf-8') as f:
                data = json.load(f)
                assert count == len(data)
                assert data[0].get('network_name') == 'mainnet'
                assert data[0].get('fork_version') == '00000000'
                assert data[0].get('deposit_cli_version') == KEY_MANAGER_VERSION
            with open('./data/keystore/password.txt', encoding='utf-8') as f:
                assert len(f.readline()) == 20

            assert len(os.listdir('./data/keystore')) == count + 1
