import json
import os
import unittest

from click.testing import CliRunner
from staking_deposit.key_handling.key_derivation.mnemonic import get_mnemonic

from key_manager import KEY_MANAGER_VERSION
from key_manager.commands.create_keys import create_keys
from key_manager.language import WORD_LISTS_PATH

from .factories import faker

mnemonic = get_mnemonic(language='english', words_path=WORD_LISTS_PATH)


class TestCreateKeys(unittest.TestCase):
    def test_basic(self):
        vault = faker.eth_address()
        count = 5
        runner = CliRunner()
        args = [
            '--mnemonic',
            f'"{mnemonic}"',
            '--count',
            count,
            '--vault',
            vault,
            '--data-dir',
            './data'
        ]
        with runner.isolated_filesystem():
            os.mkdir('./data')
            config = {
                'network': 'goerli',
                'mnemonic_next_index': 0,
            }
            with open('./data/config', 'w', encoding='utf-8') as f:
                json.dump(config, f)
            result = runner.invoke(create_keys, args)
            assert result.exit_code == 0

            output = (
                'Creating validator keys:\t\t\n'
                'Generating deposit data JSON\t\t\n'
                'Exporting validator keystores\t\t\n'
                f'Done. Generated 5 keys for {vault} vault.\n'
                'Keystores saved to data/keystores file\n'
                'Deposit data saved to data/deposit_data.json file\n'
                'Next mnemonic start index saved to data/config file\n'
            )
            assert output.strip() == result.output.strip()
            with open('./data/deposit_data.json', encoding='utf-8') as f:
                data = json.load(f)
                assert count == len(data)
                assert data[0].get('network_name') == 'goerli'
                assert data[0].get('fork_version') == '00001020'
                assert data[0].get('deposit_cli_version') == KEY_MANAGER_VERSION
            with open('./data/keystores/password.txt', encoding='utf-8') as f:
                assert len(f.readline()) == 20

            assert len(os.listdir('./data/keystores')) == count + 1
