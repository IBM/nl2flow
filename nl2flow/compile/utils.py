from typing import List, Optional
from pydantic import BaseModel

import re


class Transform(BaseModel):
    source: str
    target: str


def string_transform(item: Optional[str], reference: List[Transform], hashit: bool = False) -> Optional[str]:
    if item is not None:
        if hashit:
            transform = f"hash_{str(abs(hash(item)))}"
        else:
            transform = item.lower()

            for pattern in [r"\s+", r"\"", r","]:
                transform = re.sub(pattern, "_", transform)

        if transform and transform == revert_string_transform(transform, reference) and transform != item:
            reference.append(
                Transform(
                    source=item,
                    target=transform,
                )
            )
        return transform
    else:
        return item


def revert_string_transforms(list_of_strings: List[str], reference: List[Transform]) -> List[str]:
    return [revert_string_transform(item, reference) for item in list_of_strings]


def revert_string_transform(item: str, reference: List[Transform]) -> str:
    og_items = list(filter(lambda x: item == x.target, reference))

    if not og_items:
        return item

    else:
        assert len(og_items) == 1, "There cannot be more than one mapping, something terrible has happened."

        source: str = og_items[0].source
        return source
