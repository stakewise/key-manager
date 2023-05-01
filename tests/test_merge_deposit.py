import json
import os
import tempfile

from key_manager.commands.merge_deposit import merge_deposit_files


def test_merge_deposit_files():
    file1_content = [
        {"id": 1, "pubkey": "0x1"},
        {"id": 3, "pubkey": "0x3"},
    ]
    file2_content = [
        {"id": 2, "pubkey": "0x2"},
        {"id": 4, "pubkey": "0x4"},
    ]

    with tempfile.NamedTemporaryFile('w', delete=False) as file1, \
        tempfile.NamedTemporaryFile('w', delete=False) as file2, \
        tempfile.NamedTemporaryFile('w', delete=False) as merged_file:
        json.dump(file1_content, file1)
        json.dump(file2_content, file2)

        file1.flush()
        file2.flush()

        merge_deposit_files((file1.name, file2.name), merged_file.name)

        with open(merged_file.name, 'r', encoding='utf-8') as result:
            merged_json = json.load(result)

        expected_merged_json = [
            {"id": 1, "pubkey": "0x1"},
            {"id": 2, "pubkey": "0x2"},
            {"id": 3, "pubkey": "0x3"},
            {"id": 4, "pubkey": "0x4"},
        ]

        assert merged_json == expected_merged_json

    os.remove(file1.name)