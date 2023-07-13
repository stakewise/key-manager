import json
import os
import unittest
from os import makedirs, path
from unittest.mock import patch

from click.testing import CliRunner

from key_manager.commands.update_db import update_db


class TestUpdateDB(unittest.TestCase):
    def test_basic(self):
        runner = CliRunner()

        with runner.isolated_filesystem():
            vault = '0xc7339da617B8EECa48Ff4bc34dC8a146503bC97b'

            # fmt: off
            keystores = {
                # pylint: disable-next=line-too-long
                'keystore-m_12381_3600_2_0_0.json': {'crypto': {'kdf': {'function': 'scrypt', 'params': {'dklen': 32, 'n': 262144, 'r': 8, 'p': 1, 'salt': '65ae71e6242b6e7cd33e64bf9e60d28b9811734755589b01a90c60f1117c87c4'}, 'message': ''}, 'checksum': {'function': 'sha256', 'params': {}, 'message': 'e7a63a6be491f33251310b8bf21bf10a9bcb1b80bf9b83b7aa9c257b374a7f48'}, 'cipher': {'function': 'aes-128-ctr', 'params': {'iv': '5f8f7c1cd3d1e45e6bb2301e48404ba3'}, 'message': '204e5135e4810ea12dd989254bac912c1061fe5f6bd48f96b9dd05b80a7b6402'}}, 'description': '', 'pubkey': 'b7a5e0350d134faca6e13ee2c047e77d487a918553d3c53cbcc594a9453987e6cd1a8069ffcb97331c4bebc043571cfa', 'path': 'm/12381/3600/2/0/0', 'uuid': 'cd2e2128-dd32-447f-9986-3222339d68a1', 'version': 4},
                # pylint: disable-next=line-too-long
                'keystore-m_12381_3600_1_0_0.json': {'crypto': {'kdf': {'function': 'scrypt', 'params': {'dklen': 32, 'n': 262144, 'r': 8, 'p': 1, 'salt': '65ae71e6242b6e7cd33e64bf9e60d28b9811734755589b01a90c60f1117c87c4'}, 'message': ''}, 'checksum': {'function': 'sha256', 'params': {}, 'message': 'd5b8a2545a980460cfd0fb97105913d056f32a2c616ab09a8a159f81c52ea75f'}, 'cipher': {'function': 'aes-128-ctr', 'params': {'iv': '5f8f7c1cd3d1e45e6bb2301e48404ba3'}, 'message': '570dfd8b226d55aef9f48a5d9479e14d832ac269b4b8d0591234baf0fe38b618'}}, 'description': '', 'pubkey': '80d2116f7c17fb0163c136c3cb34e2fd61a027a1475890b9fc53d0d0b804902e3deb0d4a0d42395e00d9e8b9045feb1f', 'path': 'm/12381/3600/1/0/0', 'uuid': '04fe0a28-ecb5-4a2f-913d-4087189f11f4', 'version': 4},
                # pylint: disable-next=line-too-long
                'keystore-m_12381_3600_0_0_0.json': {'crypto': {'kdf': {'function': 'scrypt', 'params': {'dklen': 32, 'n': 262144, 'r': 8, 'p': 1, 'salt': '65ae71e6242b6e7cd33e64bf9e60d28b9811734755589b01a90c60f1117c87c4'}, 'message': ''}, 'checksum': {'function': 'sha256', 'params': {}, 'message': '3774bb544df0ab714a05a013e452b422fd52432dcb2291feb669d63941a1e7f5'}, 'cipher': {'function': 'aes-128-ctr', 'params': {'iv': '5f8f7c1cd3d1e45e6bb2301e48404ba3'}, 'message': '4e155d5edff57295a06a1c59761388343a0d0c72e3d9a981e82a533169e0b2c1'}}, 'description': '', 'pubkey': 'a739c0e5746146cd23db70ff24ccd07639f6c092375de9367e278bb94da420bdb147b8649c083e8cfdc7b8735b023908', 'path': 'm/12381/3600/0/0/0', 'uuid': '319a35fb-af9e-4e16-b08b-7dbcf6e353de', 'version': 4},
            }
            # fmt: on

            public_keys = [
                # pylint: disable-next=line-too-long
                '0xa739c0e5746146cd23db70ff24ccd07639f6c092375de9367e278bb94da420bdb147b8649c083e8cfdc7b8735b023908',
                # pylint: disable-next=line-too-long
                '0x80d2116f7c17fb0163c136c3cb34e2fd61a027a1475890b9fc53d0d0b804902e3deb0d4a0d42395e00d9e8b9045feb1f',
                # pylint: disable-next=line-too-long
                '0xb7a5e0350d134faca6e13ee2c047e77d487a918553d3c53cbcc594a9453987e6cd1a8069ffcb97331c4bebc043571cfa',
            ]
            password = 'i@uNh!dl!95r^Hm65t93'
            keystores_dir = './test_data/keystores/'
            keystores_password_file = './test_data/password.txt'

            makedirs(path.abspath(keystores_dir), exist_ok=True)
            with open(keystores_password_file, 'w', encoding='utf-8') as f:
                f.write(password)
            for filename, content in keystores.items():
                with open(os.path.join(str(keystores_dir), filename), 'w', encoding='utf-8') as f:
                    json.dump(content, f)

            db_url = 'postgresql://username:pass@hostname/dbname'
            args = [
                '--keystores-dir',
                keystores_dir,
                '--keystores-password-file',
                keystores_password_file,
                '--db-url',
                db_url,
                '--no-confirm',
                '--vault',
                vault,
            ]
            with patch('key_manager.commands.update_db.check_db_connection'), patch(
                'key_manager.commands.update_db.Database.fetch_public_keys_count',
                return_value=len(keystores),
            ), patch(
                'key_manager.commands.update_db.Database.upload_keys',
                return_value=None,
            ) as db_upload_mock:
                result = runner.invoke(update_db, args)
                assert (
                    f'The database contains {len(keystores)} validator keys.'
                    in result.output.strip()
                )
                db_upload_mock.assert_called_once()
                results = db_upload_mock.call_args.kwargs['keys']
                assert sorted([x.public_key for x in results]) == sorted(public_keys)

                result = runner.invoke(update_db, args)

                assert (
                    f'The database contains {len(keystores)} validator keys.'
                    in result.output.strip()
                )
