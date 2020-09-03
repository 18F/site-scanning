"""
errors.py

Following the Microsoft REST API Guidelines[1], errors is for API behaviors that fit
the following definition:

"Errors, or more specifically Service Errors, are defined as a client passing invalid
data to the service and the service correctly rejecting that data. Examples include invalid
credentials, incorrect parameters, unknown version IDs, or similar. These are generally "4xx"
HTTP error codes and are the result of a client passing incorrect or invalid data.

Errors do not contribute to overall API availability."[2]

[1] https://github.com/microsoft/api-guidelines/blob/vNext/Guidelines.md
[2] https://github.com/microsoft/api-guidelines/blob/vNext/Guidelines.md#51-errors
"""


class APIError(dict):
    """
    APIError represents an error in the system to which we can intentionally respond.

    The main purpose of this class is to group error codes and provide a dictionary represenation
    of error codes corresponding to the Microsoft REST API Guidelines error taxonomy. As such,
    we subclass dict so that APIErrors act like dictionaries.

    It's best to use the classmethod factory methods to instantiate APIErrors,
        e.g., APIError.HttpNotFound(f"nothing found for {query}")
    """

    def __init__(self, error_code: str, message: str):
        super().__init__(error={"code": error_code, "message": message})
        self.error_code = error_code
        self.message = message

    @classmethod
    def HttpNotFound(cls, msg: str):
        return cls("HttpNotFound", msg)

    @classmethod
    def InternalServerError(cls):
        return cls("InternalServerError", "Internal Server Error.")
