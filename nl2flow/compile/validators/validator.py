from pydantic import BaseModel
from typing import Optional, Any

import logging


class ValidationMessage(BaseModel):
    truth_value: bool
    error_msg: Optional[str]


class Validator:
    def test_all(self, *args: Any) -> bool:
        logging.debug("Running all tests.")

        for method in dir(self):
            what_is_method = getattr(self, method)

            if (
                callable(what_is_method)
                and not method.startswith("__")
                and method != "test_all"
            ):
                logging.debug(f"Running {method}.")

                result: ValidationMessage = eval(f"self.{method}({args})")
                assert result.truth_value, result.error_msg

        return True
