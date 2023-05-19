import json
import os
import unittest

from click.testing import CliRunner
from staking_deposit.key_handling.key_derivation.mnemonic import get_mnemonic

from key_manager import KEY_MANAGER_VERSION
from key_manager.commands.create_keys import create_keys
from key_manager.commands.init import init
from key_manager.language import WORD_LISTS_PATH
from key_manager.settings import CONFIG_DIR

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
            vault
        ]
        args_init = [
            '--language',
            'english',
            '--no-verify',
            '--vault',
            vault,
            '--network',
            'goerli'
        ]
        with runner.isolated_filesystem():
            runner.invoke(init, args_init)
            result = runner.invoke(create_keys, args)
            assert result.exit_code == 0

            vault_dir = f'{CONFIG_DIR}/{vault}'

            output = (
                'Creating validator keys:\t\t\n'
                'Generating deposit data JSON\t\t\n'
                'Exporting validator keystores\t\t\n'
                f'Configuration updated in {vault_dir}/config.json\n'
                f'Done. Generated 5 keys for {vault} vault.\n'
                f'Keystores saved to {vault_dir}/keystores file\n'
                f'Deposit data saved to {vault_dir}/deposit_data.json file\n'
                f'Next mnemonic start index saved to {vault_dir}/config file\n'
            )
            assert output.strip() == result.output.strip()
            with open(f'{vault_dir}/deposit_data.json', encoding='utf-8') as f:
                data = json.load(f)
                assert count == len(data)
                assert data[0].get('network_name') == 'goerli'
                assert data[0].get('fork_version') == '00001020'
                assert data[0].get('deposit_cli_version') == KEY_MANAGER_VERSION
            with open(f'{vault_dir}/keystores/password.txt', encoding='utf-8') as f:
                assert len(f.readline()) == 20

            assert len(os.listdir(f'{vault_dir}/keystores')) == count + 1
