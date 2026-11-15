"""Shared key code mappings for CEF input events.

Used by both BrowserSession (human input) and ComputerTool (AI agent input).
"""

from __future__ import annotations

import sys


def build_native_keycode_map() -> dict[int, int]:
    """Map JS keyCode (Windows VK codes) to platform-specific native key codes.

    CEF uses native_key_code for editing commands (deleteBackward, etc.)
    on macOS. On Linux it uses X11 key codes. On Windows, windows_key_code
    is primary so native_key_code is less critical.
    """
    if sys.platform == "darwin":
        return {
            8: 51,
            9: 48,
            13: 36,
            27: 53,
            37: 123,
            38: 126,
            39: 124,
            40: 125,
            46: 117,
            33: 116,
            34: 121,
            35: 119,
            36: 115,
        }
    elif sys.platform == "linux":
        return {
            8: 22,
            9: 23,
            13: 36,
            27: 9,
            37: 113,
            38: 111,
            39: 114,
            40: 116,
            46: 119,
            33: 112,
            34: 117,
            35: 115,
            36: 110,
        }
    else:
        return {}


NATIVE_KEY_CODES = build_native_keycode_map()

KEY_NAME_TO_VK: dict[str, int] = {

    **{chr(c): c - 32 for c in range(ord("a"), ord("z") + 1)},

    **{str(d): 0x30 + d for d in range(10)},

    "return": 13,
    "enter": 13,
    "tab": 9,
    "escape": 27,
    "esc": 27,
    "backspace": 8,
    "delete": 46,
    "space": 32,
    " ": 32,

    "arrowup": 38,
    "up": 38,
    "arrowdown": 40,
    "down": 40,
    "arrowleft": 37,
    "left": 37,
    "arrowright": 39,
    "right": 39,

    "home": 36,
    "end": 35,
    "pageup": 33,
    "page_up": 33,
    "pagedown": 34,
    "page_down": 34,

    "f1": 0x70,
    "f2": 0x71,
    "f3": 0x72,
    "f4": 0x73,
    "f5": 0x74,
    "f6": 0x75,
    "f7": 0x76,
    "f8": 0x77,
    "f9": 0x78,
    "f10": 0x79,
    "f11": 0x7A,
    "f12": 0x7B,

    "shift": 16,
    "control": 17,
    "ctrl": 17,
    "alt": 18,
    "meta": 91,
    "super": 91,
    "command": 91,
    "cmd": 91,

    ";": 186,
    "=": 187,
    ",": 188,
    "-": 189,
    ".": 190,
    "/": 191,
    "`": 192,
    "[": 219,
    "\\": 220,
    "]": 221,
    "'": 222,
}



SHIFTED_CHAR_TO_VK: dict[str, int] = {
    "!": 0x31,
    "@": 0x32,
    "#": 0x33,
    "$": 0x34,
    "%": 0x35,
    "^": 0x36,
    "&": 0x37,
    "*": 0x38,
    "(": 0x39,
    ")": 0x30,
    "_": 189,
    "+": 187,
    "{": 219,
    "}": 221,
    "|": 220,
    ":": 186,
    '"': 222,
    "<": 188,
    ">": 190,
    "?": 191,
    "~": 192,
}


MOD_SHIFT = 1 << 1
MOD_CTRL = 1 << 2
MOD_ALT = 1 << 3
MOD_META = 1 << 7

MODIFIER_MAP: dict[str, int] = {
    "shift": MOD_SHIFT,
    "control": MOD_CTRL,
    "ctrl": MOD_CTRL,
    "alt": MOD_ALT,
    "option": MOD_ALT,
    "meta": MOD_META,
    "super": MOD_META,
    "command": MOD_META,
    "cmd": MOD_META,
}


RAWKEYDOWN = 0
KEYUP = 2
CHAR = 3


NON_CHAR_KEYS = {
    8,
    9,
    13,
    27,
    37,
    38,
    39,
    40,
    33,
    34,
    35,
    36,
    46,
    16,
    17,
    18,
    91,
    *range(0x70, 0x7C),
}
