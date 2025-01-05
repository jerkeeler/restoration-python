import string

OUTER_HIERARCHY_START_OFFSET = 257
DATA_OFFSET = 6
MAX_SCAN_LENGTH = 50

UPPERCASE_ASSCII = set(bytes(string.ascii_uppercase, "utf-8")) | set(bytes(string.digits, "utf-8"))
