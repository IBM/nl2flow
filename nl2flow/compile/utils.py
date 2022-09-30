from typing import List
from pydantic import BaseModel

import re


class Transform(BaseModel):
    source: str
    target: str


def string_transform(item: str) -> str:
    return re.sub(r"\s+", "_", item.lower())


def revert_string_transform(item: str, reference: List[Transform]) -> str:
    og_items = list(filter(lambda x: item == x.target, reference))
    assert (
        len(og_items) == 1
    ), "There cannot be more than one mapping, something terrible has happened."

    source: str = og_items[0].source
    return source
