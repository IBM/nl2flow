import hashlib
import json
from typing import Any, Dict


def get_hash(data: Dict[Any, Any]) -> str:
    dhash = hashlib.md5()
    dhash.update(json.dumps(data, sort_keys=True).encode())
    return dhash.hexdigest()


def get_hash_str(input: str) -> str:
    return str(hash(input))
