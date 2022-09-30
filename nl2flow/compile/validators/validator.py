from pydantic import BaseModel
from typing import Optional, Any

import logging


class ValidationMessage(BaseModel):
    truth_value: bool
    error_message: Optional[str]


class Validator:
    @classmethod
    def test_all(cls, args: Any) -> bool:
        logging.info("Running all tests.")

        for method in dir(cls):
            what_is_method = getattr(cls, method)

            if (
                callable(what_is_method)
                and not method.startswith("__")
                and method != "test_all"
            ):
                logging.info(f"Running {method}.")

                result: ValidationMessage = what_is_method(args)
                assert result.truth_value, f"{method}: {result.error_message}"

        return True
