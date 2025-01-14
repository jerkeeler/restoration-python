import string

OUTER_HIERARCHY_START_OFFSET = 257
DATA_OFFSET = 6
MAX_SCAN_LENGTH = 50

UPPERCASE_ASCII = set(bytes(string.ascii_uppercase, "utf-8")) | set(bytes(string.digits, "utf-8"))
ASCII = set(bytes(string.ascii_letters + string.digits, "utf-8"))
FOOTER = bytes([0, 1, 0, 0, 0, 0, 0, 0])
