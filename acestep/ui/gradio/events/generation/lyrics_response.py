"""Validate lyric-format responses before replacing the user's words."""
import re


def clean_lyrics_response(text, caption):
    """Extract an explicit lyric section and reject caption-only or metadata output."""
    text = str(text or "").strip()
    if "</think>" in text:
        text = text.split("</think>", 1)[1].strip()
    match = re.search(r"(?im)^\s*#{1,3}\s*lyrics?\s*:?[ \t]*$", text)
    if match:
        text = text[match.end():].strip()
        text = re.split(r"(?im)^\s*#{1,3}\s+(?:caption|description|metadata)\b", text)[0].strip()
    elif re.search(r"(?im)^\s*(?:#{1,3}\s*)?(?:caption|description|bpm|duration|keyscale)\s*[:\n]", text):
        return None
    text = text.removesuffix("<|im_end|>").strip()
    if not text or text.casefold() == str(caption or "").strip().casefold():
        return None
    return text
