#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

from typing import Annotated
from uuid import uuid4

from fastapi import Depends
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.common.log import log
from backend.common.model import MappedBase
from backend.core.conf import settings
from pydantic import AnyUrl, SecretStr
from typing import Optional


def create_engine_and_session(url: str | URL):
    try:
        # 数据库引擎
        engine = create_async_engine(url, echo=settings.MYSQL_ECHO, future=True, pool_pre_ping=True)
        # log.success('数据库连接成功')
    except Exception as e:
        log.error('❌ 数据库链接失败 {}', e)
        sys.exit()
    else:
        db_session = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        return engine, db_session

def build_database_uri(scheme: str, username: str, password: str, host: str, port: int, path: str) -> AnyUrl:
    try:
        return str(AnyUrl.build(
            scheme=scheme,
            username=username,
            password=password,
            host=host,
            port=port,
            path=f'{path}',
        ))
    except Exception as e:
        raise ValueError(f"Failed to build database URI: {e}")

def get_sql_url() -> Optional[AnyUrl]:
    sql_url = None
    if settings.SQL_TYPE == 'mysql':
        # MySQL
        sql_url = build_database_uri(
            scheme=settings.SQL_SCHEME,
            username=settings.SQL_USER,
            password=settings.SQL_PASSWORD,
            host=settings.SQL_HOST,
            port=settings.SQL_PORT,
            path=settings.SQL_DATABASE,
        )
    elif settings.SQL_TYPE == 'postgres':
        # PostgreSQL
        sql_url = build_database_uri(
            scheme="postgresql+psycopg",
            username=settings.SQL_USER,
            password=settings.SQL_PASSWORD,
            host=settings.SQL_HOST,
            port=settings.SQL_PORT,
            path=settings.SQL_DATABASE,
        )
    return sql_url


async_engine, async_db_session = create_engine_and_session(get_sql_url())


async def get_db() -> AsyncSession:
    """session 生成器"""
    session = async_db_session()
    try:
        yield session
    except Exception as se:
        await session.rollback()
        raise se
    finally:
        await session.close()


# Session Annotated
CurrentSession = Annotated[AsyncSession, Depends(get_db)]


async def create_table():
    """创建数据库表"""
    async with async_engine.begin() as coon:
        await coon.run_sync(MappedBase.metadata.create_all)


def uuid4_str() -> str:
    """数据库引擎 UUID 类型兼容性解决方案"""
    return str(uuid4())
