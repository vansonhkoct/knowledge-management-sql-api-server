"""
Global Exception Handlers

Provides centralized exception handling for the FastAPI application.
"""

import logging
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from tortoise.exceptions import DoesNotExist, IntegrityError, ValidationError as TortoiseValidationError

logger = logging.getLogger(__name__)

def setup_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers for the application."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        """Handle standard HTTP exceptions."""
        logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail,
                "error_type": "HTTPException"
            }
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request, exc: ValidationError):
        """Handle Pydantic validation errors."""
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Validation error",
                "errors": exc.errors(),
                "error_type": "ValidationError"
            }
        )

    @app.exception_handler(TortoiseValidationError)
    async def tortoise_validation_exception_handler(request, exc: TortoiseValidationError):
        """Handle Tortoise ORM validation errors."""
        logger.warning(f"Tortoise validation error: {exc}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Database validation error",
                "errors": str(exc),
                "error_type": "TortoiseValidationError"
            }
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request, exc: IntegrityError):
        """Handle database integrity constraint violations."""
        logger.error(f"Database integrity error: {exc}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Database constraint violation",
                "errors": "Data integrity violation - check constraints and unique fields",
                "error_type": "IntegrityError"
            }
        )

    @app.exception_handler(DoesNotExist)
    async def does_not_exist_handler(request, exc: DoesNotExist):
        """Handle database record not found errors."""
        logger.warning(f"Record not found: {exc}")
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": "Record not found",
                "errors": "The requested resource was not found",
                "error_type": "DoesNotExist"
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        """Handle all other unexpected exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "error_type": "InternalServerError",
                "error_id": ""  # Could add error tracking ID here
            }
        )

def create_error_response(
    message: str,
    error_type: str,
    errors: Dict[str, Any] = None,
    status_code: int = 400
) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "success": False,
        "message": message,
        "error_type": error_type,
        "errors": errors or {}
    }