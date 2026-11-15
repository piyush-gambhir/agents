import re


def split_paragraphs(text: str) -> list[tuple[str, int, int]]:
    """
    Split the text into paragraphs.
    Returns a list of paragraphs with their start and end indices of the original text.
    """

    pattern = r"\n\s*\n"

    splits = list(re.finditer(pattern, text))

    paragraphs: list[tuple[str, int, int]] = []
    start = 0

    if not splits:
        stripped = text.strip()

        if not stripped:
            return paragraphs
        start_index = text.index(stripped)
        return [(stripped, start_index, start_index + len(stripped))]

    for split in splits:
        end = split.start()
        paragraph = text[start:end].strip()
        if paragraph:
            para_start = start + text[start:end].index(paragraph)
            para_end = para_start + len(paragraph)
            paragraphs.append((paragraph, para_start, para_end))
        start = split.end()

    last_paragraph = text[start:].strip()
    if last_paragraph:
        para_start = start + text[start:].index(last_paragraph)
        para_end = para_start + len(last_paragraph)
        paragraphs.append((last_paragraph, para_start, para_end))

    return paragraphs
