import unittest
from unittest.mock import patch

from click.testing import CliRunner

from key_manager.commands.init import init

from .factories import faker

mnemonic = ' '.join([faker.word() for x in range(24)])


@patch('key_manager.language.get_mnemonic', return_value=mnemonic)
class TestCreateMnemonic(unittest.TestCase):
    def test_basic(self, mnemonic_mock):
        vault = faker.eth_address()
        runner = CliRunner()
        args = [
            '--language',
            'english',
            '--vault',
            vault,
            '--network',
            'goerli'
        ]
        result = runner.invoke(init, args, input=f'a\n{mnemonic}\n')
        assert result.exit_code == 0
        mnemonic_mock.assert_called_once()
        assert mnemonic in result.output.strip()
        assert 'Configuration' in result.output.strip()

    def test_bad_verify(self, mnemonic_mock):
        vault = faker.eth_address()
        runner = CliRunner()
        args = [
            '--language',
            'english',
            '--vault',
            vault,
            '--network',
            'goerli'
        ]
        result = runner.invoke(init, args, input=f'a\n{mnemonic} bad\na\n{mnemonic}\n')
        assert result.exit_code == 0
        mnemonic_mock.assert_called_once()
        assert mnemonic in result.output.strip()
        assert 'Configuration' in result.output.strip()

    def test_no_verify(self, mnemonic_mock):
        vault = faker.eth_address()
        runner = CliRunner()
        args = [
            '--language',
            'english',
            '--no-verify',
            '--vault',
            vault,
            '--network',
            'goerli'
        ]
        result = runner.invoke(init, args)
        assert result.exit_code == 0
        mnemonic_mock.assert_called_once()
        assert mnemonic in result.output.strip()

    def test_bad_language(self, *args):
        runner = CliRunner()
        args = ['--language', 'bad', '--no-verify']
        result = runner.invoke(init, args)
        assert result.exit_code == 2
        assert "Invalid value for '--language': 'bad' is not one of" in result.output.strip()