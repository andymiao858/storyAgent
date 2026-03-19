"""Unified API response format."""
from typing import Any, Optional


def success_response(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}


def error_response(code: int = 4000, message: str = "error", data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}
