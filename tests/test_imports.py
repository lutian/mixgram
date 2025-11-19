import pytest

def test_import_mixgram():
    import mixgram

    # Main functions should exist
    assert hasattr(mixgram, "encode_video"), "mixgram.encode_video does not exists"
    assert hasattr(mixgram, "decode_video"), "mixgram.decode_video does not exists"
