# convenience functions/electric boogaloo

from mastopy.compute import compute
from functools import lru_cache

HASH_INVALIDS = ("!", "@", "#")


@compute
@lru_cache
def detect_hashtags_in_post(content: str, include_hashtags: bool = False) -> list[str]:
    """
    Detect all hashtags inside a post, yay!

    ::args::
    content: str - the content to search through
    include_hashtags: bool - whether or not to include the hashtag symbol (#) itself, necessary if you want to call str.replace on the content, Maize!
    """
    tags: list = []
    append_hash: bool = False
    current_hash: str = ""

    for idx, char in enumerate(content):
        if char == "#" and not append_hash:
            append_hash = True
            if not include_hashtags:
                continue

        if append_hash:
            if not char.isspace():
                current_hash += char
            elif char.isspace():
                append_hash = False
                tags.append(current_hash)
                current_hash = ""

    if current_hash != "":
        tags.append(current_hash)

    return tags
