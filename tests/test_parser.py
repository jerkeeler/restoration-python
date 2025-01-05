import io
import struct
import zlib

import pytest

from restoration.consts import DATA_OFFSET
from restoration.parser import (
    decompressl33t,
    find_two_letter_seq,
    read_bool,
    read_build_string,
    read_int,
    read_string,
)
from restoration.types import Node
from restoration.xceptions import NodeNotFound


def test_decompressl33t_valid():
    # Prepare a valid l33t-encoded stream
    compressed_data = zlib.compress(b"hello world")
    header = b"l33t"
    length = struct.pack("<i", len(compressed_data))

    stream = io.BytesIO(header + length + compressed_data)

    result = decompressl33t(stream)

    assert result == b"hello world"


def test_decompressl33t_invalid_header():
    # Prepare a stream with an invalid header
    invalid_header = b"abcd"
    compressed_data = zlib.compress(b"hello world")
    length = struct.pack("<i", len(compressed_data))

    stream = io.BytesIO(invalid_header + length + compressed_data)

    with pytest.raises(ValueError, match="Invalid header. Expecting 'l33t'"):
        decompressl33t(stream)


def test_decompressl33t_empty_stream():
    # Prepare an empty stream
    stream = io.BytesIO(b"")

    with pytest.raises(ValueError, match="Invalid header. Expecting 'l33t'"):
        decompressl33t(stream)


def test_decompressl33t_partial_data():
    # Prepare a stream with an incomplete length or data
    header = b"l33t"
    length = struct.pack("<i", 1000)  # Large length that exceeds actual data
    stream = io.BytesIO(header + length + b"incomplete_data")

    with pytest.raises(zlib.error):  # zlib.error expected for incomplete data
        decompressl33t(stream)


def test_end_offset():
    node = Node(token="A", offset=5, size=15)
    assert node.end_offset == 20 + DATA_OFFSET


def test_path_root_node():
    node = Node(token="A", offset=0, size=10)
    assert node.path == "A"


def test_path_child_node():
    parent = Node(token="A", offset=0, size=10)
    child = Node(token="B", offset=10, size=5, parent=parent)
    assert child.path == "A/B"


def test_get_children_single():
    parent = Node(token="A", offset=0, size=10)
    child = Node(token="B", offset=10, size=5, parent=parent)
    parent.children.append(child)

    result = parent.get_children(["B"])
    assert result == [child]


def test_get_children_multiple():
    parent = Node(token="A", offset=0, size=10)
    child1 = Node(token="B", offset=10, size=5, parent=parent)
    child2 = Node(token="B", offset=15, size=5, parent=parent)
    parent.children.extend([child1, child2])

    result = parent.get_children(["B"])
    assert result == [child1, child2]


def test_get_children_nested():
    root = Node(token="A", offset=0, size=10)
    child1 = Node(token="B", offset=10, size=5, parent=root)
    child2 = Node(token="C", offset=15, size=5, parent=child1)
    root.children.append(child1)
    child1.children.append(child2)

    result = root.get_children(["B", "C"])
    assert result == [child2]


def test_str_representation():
    node = Node(token="A", offset=5, size=15)
    expected_str = "A -- offset=5, end_offset=26 size=15, children=0"
    assert str(node) == expected_str


# Tests for read_int and read_bool
def test_read_int():
    data = b"\x01\x02\x03\x04"
    assert read_int(data, 0) == 513  # 0x0201 in little-endian
    assert read_int(data, 2) == 1027  # 0x0403 in little-endian


def test_read_bool():
    data = b"\x01\x00\x01"
    assert read_bool(data, 0) is True
    assert read_bool(data, 1) is False
    assert read_bool(data, 2) is True


# Tests for read_string
def test_read_string():
    data = b"\x05\x00\x00\x00H\x00e\x00l\x00l\x00o\x00"
    string, next_offset = read_string(data, 0)
    assert string == "Hello"
    assert next_offset == 14


def test_read_build_string_success():
    # Create root node and FH child node
    fh_node = Node(token="FH", offset=-6, size=10)  # Using -6 offset to ensure the string is read correctly
    root_node = Node(token="ROOT", offset=0, size=20, children=[fh_node])

    # Mock the data
    data = b"\x02\x00\x00\x00H\x00i\x00\x00\x00"  # "Hi" encoded in UTF-16-LE

    # Test the function
    result = read_build_string(root_node, data)

    # Assertions
    assert result == "Hi"


def test_read_build_string_no_fh_node():
    # Create root node without FH nodes
    root_node = Node(token="ROOT", offset=0, size=20)

    # Mock data
    data = b""

    # Test the function
    with pytest.raises(NodeNotFound, match="Could not find FH node! No build string!"):
        read_build_string(root_node, data)


def test_read_build_string_multiple_fh_nodes():
    # Create root node with multiple FH child nodes
    fh_node_1 = Node(token="FH", offset=-6, size=10)  # Using -6 offset to ensure the string is read correctly
    fh_node_2 = Node(token="FH", offset=20, size=10)
    root_node = Node(token="ROOT", offset=0, size=30, children=[fh_node_1, fh_node_2])

    # Mock the data
    data = b"\x02\x00\x00\x00H\x00i\x00\x00\x00"  # "Hi" encoded in UTF-16-LE

    # Test the function
    result = read_build_string(root_node, data)

    # Assertions
    assert result == "Hi"


def test_find_two_letter_seq():
    # Basic test case
    data = b"xxYZabc"
    assert find_two_letter_seq(data) == 2

    # Test with offset
    assert find_two_letter_seq(data, offset=1) == 2

    # Test with upper_bound
    assert find_two_letter_seq(data, upper_bound=-1) == -1

    # Test when no uppercase sequence exists
    data = b"xxxxabc"
    assert find_two_letter_seq(data) == -1

    # Test when sequence is near the end
    data = b"abcdEF"
    assert find_two_letter_seq(data) == 4

    # Test when sequence is exactly at the boundary
    data = b"XxYzEF"
    assert find_two_letter_seq(data, offset=3, upper_bound=6) == 4

    # Test exceeding MAX_SCAN_LENGTH
    long_data = b"x" * 51 + b"AB"
    assert find_two_letter_seq(long_data) == -1

    # Edge case: empty data
    assert find_two_letter_seq(b"") == -1

    # Edge case: data smaller than required size
    assert find_two_letter_seq(b"A") == -1
    assert find_two_letter_seq(b"AB", offset=1) == -1
