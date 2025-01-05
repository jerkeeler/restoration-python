import json
from dataclasses import dataclass, field
from functools import cached_property

from restoration.consts import DATA_OFFSET

PROFILE_KEY_VALUE_TPYES = None | str | bool | int


@dataclass
class Replay:
    data: bytes
    header_root_node: "Node"
    game_commands: list
    build_string: str
    profile_keys: dict[str, PROFILE_KEY_VALUE_TPYES]

    def to_dict(self) -> dict:
        return {"build_string": self.build_string, "profile_keys": self.profile_keys}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=4)


@dataclass
class Node:
    token: str
    offset: int
    size: int
    parsed: bool = False
    parent: "Node | None" = None
    children: list["Node"] = field(default_factory=list)

    @cached_property
    def end_offset(self):
        return self.offset + self.size + DATA_OFFSET

    @cached_property
    def path(self) -> str:
        """
        A string representing the "path" of the node based on its and its parents tokens. For example, if this node
        has a token of JK and the parent is AB the path would be AB/JK.
        """
        if self.parent is None:
            return self.token
        return f"{self.parent.path}/{self.token}"

    def get_children(self, path: list[str]) -> list["Node"]:
        """
        Get the children of this node that match the give path. Some paths have more than one node. For example, there
        are multiple nodes with the XN/XN/XN path.
        """
        if not path:
            return [self]

        nodes = []
        for child in self.children:
            if child.token == path[0]:
                nodes.extend(child.get_children(path[1:]))

        return nodes

    def __str__(self) -> str:
        """
        Making it easer to debug.
        """
        return (
            f"{self.path} -- offset={self.offset}, end_offset={self.end_offset} "
            f"size={self.size}, children={len(self.children)}"
        )

    def print(self) -> None:
        """
        Prints the tree structure of the node and its children.
        """
        print(self)
        for child in self.children:
            child.print()
