from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from app.core.response import build_response


async def http_exception_handler(request: Request, exc: HTTPException):
    return build_response(
        status_code=exc.status_code,
        data=None,
        message=exc.detail,
        request=request,
        error=exc.detail,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return build_response(
        status_code=422,
        data=None,
        message="Dữ liệu không hợp lệ",
        request=request,
        error=exc.errors(),
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return build_response(
        status_code=500,
        data=None,
        message="Lỗi hệ thống, vui lòng thử lại sau",
        request=request,
        error=str(exc),
    )
