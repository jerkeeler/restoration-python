from restoration.utils import read_bool, read_short


# Tests for read_int and read_bool
def test_read_int():
    data = b"\x01\x02\x03\x04"
    assert read_short(data, 0) == 513  # 0x0201 in little-endian
    assert read_short(data, 2) == 1027  # 0x0403 in little-endian


def test_read_bool():
    data = b"\x01\x00\x01"
    assert read_bool(data, 0) is True
    assert read_bool(data, 1) is False
    assert read_bool(data, 2) is True
