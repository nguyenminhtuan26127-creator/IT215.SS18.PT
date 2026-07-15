from datetime import datetime
from typing import Any, Optional
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def build_response(
    status_code: int,
    data: Any = None,
    message: str = "",
    request: Optional[Request] = None,
    error: Any = None,
):
    return JSONResponse(
        status_code=status_code,
        content={
            "statusCode": status_code,
            "data": jsonable_encoder(data) if data is not None else None,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path) if request else None,
            "error": jsonable_encoder(error) if error is not None else None,
        },
    )
