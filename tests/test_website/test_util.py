import base64
from io import BytesIO
from typing import TextIO

import argon2
import pytest

from website import util


import io
from tink import aead, JsonKeysetReader, BinaryKeysetWriter, BinaryKeysetReader
from tink import tink_config
from tink import JsonKeysetWriter


def keyset_to_json(ks):
    string_out = io.StringIO()
    writer = JsonKeysetWriter(string_out)
    writer.write(ks)
    return string_out.getvalue()


def json_to_keyset(ser):
    return JsonKeysetReader(ser).read()


def keyset_to_binary(ks):
    buff = io.BytesIO()
    BinaryKeysetWriter(buff).write(ks)
    return buff.getvalue()


def binary_to_keyset(ser):
    return BinaryKeysetReader(ser).read()

from argon2 import PasswordHasher, extract_parameters


@pytest.mark.asyncio
async def test_tink_create_keyset():
    # aead.register()
    tink_config.register()

    auth_len = 32
    conf_len = 32

    password = "password123"
    salt = b"salt"*8
    ph = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1, hash_len=auth_len+conf_len, salt_len=len(salt), encoding="utf-8", type=argon2.Type.ID)
    result = ph.hash(password, salt=salt)
    params = extract_parameters(result)

    # x = result.split("$")
    # hash = base64.b64decode(x[5])
    ph = PasswordHasher()
    assert ph.verify(result, password)
    print(result)

    kek = bytes.fromhex("00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff")
    keyring = util.create_keyset(kek, 0)
    a = keyset_to_binary(keyring)
    b = binary_to_keyset(a)

    c = keyset_to_json(keyring)
    d = json_to_keyset(c)

    print(a)
    print(c)
