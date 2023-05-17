import hashlib
import json
from typing import Dict


def get_hash(data: Dict) -> str:
    dhash = hashlib.md5()
    dhash.update(json.dumps(data, sort_keys=True).encode())
    return dhash.hexdigest()
