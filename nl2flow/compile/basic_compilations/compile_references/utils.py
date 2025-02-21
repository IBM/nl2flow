from typing import Any, Optional
from nestful.utils import get_token


def get_token_predicate_name(index: int, token: Optional[str] = None) -> str:
    token = str(get_token(index, token or "token"))
    return token


def set_token_predicate(compilation: Any, index: int) -> Any:
    token_predicate_name = get_token_predicate_name(index)
    token_predicate = compilation.lang.predicate(token_predicate_name)
    setattr(compilation, token_predicate_name, token_predicate)

    return token_predicate


def get_token_predicate(compilation: Any, index: int) -> Any:
    token_predicate_name = get_token_predicate_name(index)
    attr = getattr(compilation, token_predicate_name, None)

    if attr:
        return attr()
    else:
        return set_token_predicate(compilation, index)()
