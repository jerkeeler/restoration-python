import struct


def read_uint(data: bytes, offset: int) -> int:
    return struct.unpack("<I", data[offset : offset + 4])[0]


def read_short(data: bytes, offset: int) -> int:
    return struct.unpack("<H", data[offset : offset + 2])[0]


def read_bool(data: bytes, offset: int) -> bool:
    return struct.unpack("<?", data[offset : offset + 1])[0]
