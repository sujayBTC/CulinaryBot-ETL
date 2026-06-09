from typing import Annotated, Any, TypedDict

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
)

PHONE_NUMBER = "phone_number"
USER_ID = "user_id"
STATUS = "status"

DATA_FIELD = "data"
STATUS_FIELD = "status"
ERROR_FIELD = "error"
REQUEST_ID_FIELD = "request_id"
GENERIC_ERROR_MESSAGE = "An internal error occurred. Please try again later."
STATUS_OK = "OK"
STATUS_ERROR = "ERROR"
FIELD_NOT_FOUND_IN_MODEL = "FIELD NOT FOUND IN MODEL"
INVALID_FIELDS = "INVALID FIELDS"
NOT_FOUND = "NOT FOUND"


def create_service_success_response(data):
    return {STATUS_FIELD: STATUS_OK, DATA_FIELD: data}

def create_service_failure_response(error):
    return {STATUS_FIELD: STATUS_ERROR, DATA_FIELD: error}


ChatMessage = Annotated[HumanMessage | AIMessage, "Chat message"]


class AgentState(TypedDict, total=False):
    phone_number: str
    total_recipes: list
    total_chunks: int
    last_procced_chunk: int
    errors: Any