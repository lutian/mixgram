import sys, math
import zlib
import hashlib
from typing import Tuple

sys.set_int_max_str_digits(65536)

DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"


# -------------------------
# Inteiros <-> base36
# -------------------------
def int_to_base36(n: int) -> str:
    """Converte inteiro n >= 0 para string em base36."""
    if n < 0:
        raise ValueError("n deve ser >= 0")
    if n == 0:
        return "0"
    s = []
    while n:
        n, r = divmod(n, 36)
        s.append(DIGITS[r])
    return "".join(reversed(s))


def base36_to_int(s: str) -> int:
    """Converte string base36 para inteiro."""
    if not s:
        return 0
    return int(s, 36)


# -------------------------
# Bytes <-> base36
# -------------------------
def bytes_to_base36(b: bytes) -> str:
    """Converte bytes em big-endian para string base36."""
    if not isinstance(b, (bytes, bytearray)):
        raise TypeError("b precisa ser bytes/bytearray")
    if len(b) == 0:
        return "0"
    i = int.from_bytes(b, byteorder="big", signed=False)
    if i == 0:
        return "0"
    s = []
    while i:
        i, r = divmod(i, 36)
        s.append(DIGITS[r])
    return "".join(reversed(s))


def base36_to_bytes(s: str) -> bytes:
    """Converte base36 para bytes no tamanho mínimo necessário."""
    if not s:
        return b"\x00"
    i = int(s, 36)
    length = max(1, math.ceil(i.bit_length() / 8))
    return i.to_bytes(length, byteorder="big")


def pad_left_bytes(b: bytes, expected_len: int) -> bytes:
    """Preenche com zeros à esquerda até atingir expected_len."""
    if expected_len <= len(b):
        return b
    return (b"\x00" * (expected_len - len(b))) + b


# -------------------------
# Compressão / Descompressão
# -------------------------
def compress_bytes(b: bytes, level: int = 6) -> bytes:
    if not isinstance(b, (bytes, bytearray)):
        raise TypeError("b precisa ser bytes/bytearray")
    return zlib.compress(b, level)


def decompress_bytes(b: bytes) -> bytes:
    if not isinstance(b, (bytes, bytearray)):
        raise TypeError("b precisa ser bytes/bytearray")
    return zlib.decompress(b)


# -------------------------
# Hash
# -------------------------
def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ========================================================
# ---- NOVAS FUNÇÕES (para facilitar encode/decode) ------
# ========================================================

def encode_blob_to_b36_with_len(blob: bytes) -> Tuple[str, int]:
    """
    Converte qualquer blob de bytes em:
        (string_base36, comprimento_original_em_bytes)

    Isso permite reconstruir perfeitamente o blob depois.
    """
    if not isinstance(blob, (bytes, bytearray)):
        raise TypeError("blob precisa ser bytes/bytearray")

    original_len = len(blob)
    b36 = bytes_to_base36(blob)
    return b36, original_len


def decode_b36_with_len(b36: str, expected_len: int) -> bytes:
    """
    Inverso de encode_blob_to_b36_with_len.
    Converte base36 → bytes e restaura o tamanho exato via padding à esquerda.
    """
    raw = base36_to_bytes(b36)
    raw = pad_left_bytes(raw, expected_len)
    return raw


# -------------------------
# Teste rápido
# -------------------------
#def _self_test_roundtrip():
#    sample = b"\x00\x00\x01hello\x00"
#    b36, n = encode_blob_to_b36_with_len(sample)
#    restored = decode_b36_with_len(b36, n)
#    assert restored == sample
#
#    comp = compress_bytes(b"olá mundo")
#    dec = decompress_bytes(comp)
#    assert dec == b"ol\xc3\xa1 mundo"
#
#    print("utils.self_test OK")
#
#
#if _name_ == "_main_":
#    _self_test_roundtrip()