import struct


def read_int32(data: bytes, offset: int) -> int:
    return struct.unpack("<i", data[offset : offset + 4])[0]


def read_short(data: bytes, offset: int) -> int:
    return struct.unpack("<H", data[offset : offset + 2])[0]


def read_bool(data: bytes, offset: int) -> bool:
    return struct.unpack("<?", data[offset : offset + 1])[0]


def read_string(data: bytes, offset: int) -> tuple[str, int]:
    """
    Reads the utf-16 little endian encoded at the given offset. Strings are enocde such that the first 2 bytes
    are an unsigned integer indicating the number of characters in the string. The next 2 bytes are null padding.
    Then the string follows. Since the strings are unicode enocode each character takes up 2 bytes.
    For example a string might look like:
    \x02\x00\x00\x00H\x00e\x00l\x00l\x00o\x00

    Returns the string and the index directly after the string.
    """
    num_chars = read_short(data, offset)
    start_of_string = offset + 4  # offset + 2 bytes for int + 2 bytes of padding
    end_of_string = start_of_string + num_chars * 2
    # Characters are defined with 2 bytes using utf-16 little endian encoding, so multiple by 2 to get the number
    # of bytes to read
    raw_string = data[start_of_string:end_of_string]
    s = raw_string.decode("utf-16-le")
    return s, end_of_string
