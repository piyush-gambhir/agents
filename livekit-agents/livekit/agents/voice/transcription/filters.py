import re
from collections.abc import AsyncIterable

LINE_PATTERNS = [
    (re.compile(r"^#{1,6}\s+", re.MULTILINE), ""),
    (re.compile(r"^\s*[-+*]\s+", re.MULTILINE), ""),
    (re.compile(r"^\s*>\s+", re.MULTILINE), ""),
]

INLINE_PATTERNS = [
    (re.compile(r"!\[([^\]]*)\]\([^)]*\)"), r"\1"),
    (re.compile(r"\[([^\]]*)\]\([^)]*\)"), r"\1"),
    (re.compile(r"(?<![\w*])\*\*(?!\s)([^*\n]+?)(?<!\s)\*\*(?![\w*])"), r"\1"),
    (re.compile(r"(?<![\w*])\*(?!\s|\*)([^*\n]+?)(?<!\s)\*(?![\w*])"), r"\1"),
    (re.compile(r"(?<!\w)__([^_]+?)__(?!\w)"), r"\1"),
    (re.compile(r"(?<!\w)_([^_]+?)_(?!\w)"), r"\1"),
    (re.compile(r"`{3,4}[\S]*"), ""),
    (re.compile(r"`([^`]+?)`"), r"\1"),
    (re.compile(r"~~(?!\s)([^~]*?)(?<!\s)~~"), ""),
]
INLINE_SPLIT_TOKENS = " ,.?!;，。？！；"

COMPLETE_LINKS_PATTERN = re.compile(r"\[[^\]]*\]\([^)]*\)")
COMPLETE_IMAGES_PATTERN = re.compile(r"!\[[^\]]*\]\([^)]*\)")


async def filter_markdown(text: AsyncIterable[str]) -> AsyncIterable[str]:
    """
    Filter out markdown symbols from the text.
    """

    def has_incomplete_pattern(buffer: str) -> bool:
        """Check if buffer might contain incomplete markdown patterns that need more text."""

        if buffer.endswith(("#", "-", "+", "*", ">", "!", "`", "~", " ")):
            return True

        double_asterisks = buffer.count("**")
        if double_asterisks % 2 == 1:
            return True

        single_asterisks = buffer.count("*") - (double_asterisks * 2)
        if single_asterisks % 2 == 1:
            return True

        double_underscores = buffer.count("__")
        if double_underscores % 2 == 1:
            return True
        single_underscores = buffer.count("_") - (double_underscores * 2)
        if single_underscores % 2 == 1:
            return True

        backticks = buffer.count("`")
        if backticks % 2 == 1:
            return True

        double_tildes = buffer.count("~~")
        if double_tildes % 2 == 1:
            return True

        open_brackets = buffer.count("[")
        complete_links = len(COMPLETE_LINKS_PATTERN.findall(buffer))
        complete_images = len(COMPLETE_IMAGES_PATTERN.findall(buffer))

        remaining_brackets = open_brackets - complete_links - complete_images
        if remaining_brackets > 0:
            return True

        return False

    def process_complete_text(text: str, is_newline: bool = False) -> str:
        if is_newline:
            for pattern, replacement in LINE_PATTERNS:
                text = pattern.sub(replacement, text)

        for pattern, replacement in INLINE_PATTERNS:
            text = pattern.sub(replacement, text)

        return text

    buffer = ""
    buffer_is_newline = True

    async for chunk in text:
        buffer += chunk

        if "\n" in buffer:
            lines = buffer.split("\n")
            buffer = lines[-1]

            for i, line in enumerate(lines[:-1]):
                is_newline = buffer_is_newline if i == 0 else True
                processed_line = process_complete_text(line, is_newline=is_newline)
                yield processed_line + "\n"

            buffer_is_newline = True
            continue

        last_split_pos = 0
        for token in INLINE_SPLIT_TOKENS:
            last_split_pos = max(last_split_pos, buffer.rfind(token, last_split_pos))
            if last_split_pos >= len(buffer) - 1:
                break

        if last_split_pos >= 1:
            processable = buffer[:last_split_pos]
            rest = buffer[last_split_pos:]
            if not has_incomplete_pattern(processable):
                yield process_complete_text(processable, is_newline=buffer_is_newline)
                buffer = rest
                buffer_is_newline = False

    if buffer:
        yield process_complete_text(buffer, is_newline=buffer_is_newline)


EMOJI_PATTERN = re.compile(
    r"[\U0001F000-\U0001FBFF]"
    r"|[\U00002600-\U000026FF]"
    r"|[\U00002700-\U000027BF]"
    r"|[\U00002B00-\U00002BFF]"
    r"|[\U0000FE00-\U0000FE0F]"
    r"|\U0000200D"
    r"|\U000020E3"
    r"+",
    re.UNICODE,
)


async def filter_emoji(text: AsyncIterable[str]) -> AsyncIterable[str]:
    """
    Filter out emojis from the text.
    """

    async for chunk in text:
        filtered_chunk = EMOJI_PATTERN.sub("", chunk)
        yield filtered_chunk
