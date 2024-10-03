from typing import Any


def get_token_predicate_name(index: int, token: str = "token") -> str:
    return f"{token}{index}"


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
