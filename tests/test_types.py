from restoration.consts import DATA_OFFSET
from restoration.types import Node


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
