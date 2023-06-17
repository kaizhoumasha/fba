#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from uvicorn.protocols.http.h11_impl import STATUS_PHRASES

from backend.app.common.exception.errors import BaseExceptionMixin
from backend.app.common.log import log
from backend.app.common.response.response_schema import response_base
from backend.app.core.conf import settings


def _get_exception_code(status_code):
    """
    获取返回状态码, OpenAPI, Uvicorn... 可用状态码基于 RFC 定义, 详细代码见下方链接

    `python 状态码标准支持 <https://github.com/python/cpython/blob/6e3cc72afeaee2532b4327776501eb8234ac787b/Lib/http
    /__init__.py#L7>`__

    `IANA 状态码注册表 <https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml>`__

    :param status_code:
    :return:
    """
    try:
        STATUS_PHRASES[status_code]
    except Exception:
        code = 400
    else:
        code = status_code
    return code


def register_exception(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        全局HTTP异常处理

        :param request:
        :param exc:
        :return:
        """
        content = {'code': exc.status_code, 'msg': exc.detail}
        request.state.__request_http_exception__ = content  # 用于在中间件中获取异常信息
        return JSONResponse(
            status_code=_get_exception_code(exc.status_code),
            content=await response_base.fail(**content),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        数据验证异常处理

        :param request:
        :param exc:
        :return:
        """
        message = ''
        data = {}
        for raw_error in exc.raw_errors:
            if isinstance(raw_error.exc, ValidationError):
                exc = raw_error.exc
                if hasattr(exc, 'model'):
                    fields = exc.model.__dict__.get('__fields__')
                    for field_key in fields.keys():
                        field_title = fields.get(field_key).field_info.title
                        data[field_key] = field_title if field_title else field_key
                errors_len = len(exc.errors())
                for error in exc.errors():
                    field = str(error.get('loc')[-1])
                    _msg = error.get('msg')
                    errors_len = errors_len - 1
                    message += (
                        f'{data.get(field, field) if field != "__root__" else ""} {_msg}' + ', '
                        if errors_len > 0
                        else f'{data.get(field, field) if field != "__root__" else ""} {_msg}' + '.'
                    )
            elif isinstance(raw_error.exc, json.JSONDecodeError):
                message += 'json解析失败'
        content = {
            'code': 422,
            'msg': '请求参数非法' if len(message) == 0 else f'请求参数非法: {message}',
            'data': {'errors': exc.errors()} if message == '' and settings.UVICORN_RELOAD is True else None,
        }
        request.state.__request_validation_exception__ = content  # 用于在中间件中获取异常信息
        return JSONResponse(status_code=422, content=await response_base.fail(**content))

    @app.exception_handler(Exception)
    async def all_exception_handler(request: Request, exc: Exception):
        """
        全局异常处理

        :param request:
        :param exc:
        :return:
        """
        if isinstance(exc, BaseExceptionMixin):
            return JSONResponse(
                status_code=_get_exception_code(exc.code),
                content=await response_base.fail(code=exc.code, msg=str(exc.msg), data=exc.data if exc.data else None),
                background=exc.background,
            )

        elif isinstance(exc, AssertionError):
            return JSONResponse(
                status_code=500,
                content=await response_base.fail(
                    code=500,
                    msg=','.join(exc.args)
                    if exc.args
                    else exc.__repr__()
                    if not exc.__repr__().startswith('AssertionError()')
                    else exc.__doc__,
                )
                if settings.ENVIRONMENT == 'dev'
                else await response_base.fail(code=500, msg='Internal Server Error'),
            )

        else:
            import traceback

            log.error(f'未知异常: {exc}')
            log.error(traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content=await response_base.fail(code=500, msg=str(exc))
                if settings.ENVIRONMENT == 'dev'
                else await response_base.fail(code=500, msg='Internal Server Error'),
            )
