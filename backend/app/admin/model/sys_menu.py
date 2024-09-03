#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Union

from sqlalchemy import ForeignKey, String
from backend.core.conf import settings
if(settings.SQL_TYPE == 'mysql'):
    from sqlalchemy.dialects.mysql import LONGTEXT, JSON
elif(settings.SQL_TYPE == 'postgres'):
    from sqlalchemy.dialects.postgresql import TEXT as LONGTEXT, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.admin.model.sys_role_menu import sys_role_menu
from backend.common.model import Base, id_key

class MenuMeta():
   # 图标（菜单/tab）
  icon: str | None = ''
   # 标题名称
  title: str | None = ''
   # 用于路由->菜单排序
  order: int | None = 0
   # 激活图标（菜单）
  activeIcon: str | None = ''
   # 当前激活的菜单，有时候不想激活现有菜单，需要激活父级菜单时使用
  activePath: str
   # 是否固定标签页
   # @default false
  affixTab: bool = False
   # 固定标签页的顺序
   # @default 0
  affixTabOrder: int
   # 用于配置页面的权限，只有拥有对应权限的用户才能访问页面，不配置则不需要权限。
  authority: list[str] | None = []
   # 用于配置页面的徽标，会在菜单显示。
  badge: str
   # 用于配置页面的徽标类型，dot 为小红点，normal 为文本。
  badgeType: str | None = 'normal'
   # 用于配置页面的徽标颜色。'default' | 'destructive' | 'primary' | 'success' | 'warning' | str
  badgeVariants: str | None = 'success'
   # 当前路由的子级在菜单中不展现
   # @default false
  hideChildrenInMenu: bool = False
   # 当前路由在面包屑中不展现
   # @default false
  hideInBreadcrumb: bool = False
   # 当前路由在菜单中不展现
   # @default false
  hideInMenu: bool = False
   # 当前路由在标签页不展现
   # @default false
  hideInTab: bool = False
   # iframe 地址
  iframeSrc: str
   # 忽略权限，直接可以访问
   # @default false
  ignoreAccess: bool = False
   # 开启KeepAlive缓存
  keepAlive: bool | None = False
   # 外链-跳转路径
  link: str | None
   # 路由是否已经加载过
  loaded: bool | None = False
   # 标签页最大打开数量
  maxNumOfOpenTab: int | None = -1
   # 菜单可以看到，但是访问会被重定向到403
  menuVisibleWithForbidden: bool = False


class Menu(Base):
    """菜单表"""

    __tablename__ = 'sys_menu'

    id: Mapped[id_key] = mapped_column(init=False)
    name: Mapped[str] = mapped_column(String(50), comment='菜单名称')
    component: Mapped[str | None] = mapped_column(String(255), default=None, comment='组件路径')
    meta: Mapped[MenuMeta] = mapped_column(JSON, default=MenuMeta(), comment='菜单元信息')
    sort: Mapped[int] = mapped_column(default=0, comment='排序')
    path: Mapped[str | None] = mapped_column(String(200), default=None, comment='路由地址')
    redirect: Mapped[str | None] = mapped_column(String(200), default=None, comment='重定向地址')
    menu_type: Mapped[int] = mapped_column(default=0, comment='菜单类型（0目录 1菜单 2按钮）')
    perms: Mapped[str | None] = mapped_column(String(100), default=None, comment='权限标识')
    status: Mapped[int] = mapped_column(default=1, comment='菜单状态（0停用 1正常）')
    remark: Mapped[str | None] = mapped_column(LONGTEXT, default=None, comment='备注')
    # 父级菜单一对多
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey('sys_menu.id', ondelete='SET NULL'), default=None, index=True, comment='父菜单ID'
    )
    parent: Mapped[Union['Menu', None]] = relationship(init=False, back_populates='children', remote_side=[id])
    children: Mapped[list['Menu'] | None] = relationship(init=False, back_populates='parent')
    # 菜单角色多对多
    roles: Mapped[list['Role']] = relationship(  # noqa: F821
        init=False, secondary=sys_role_menu, back_populates='menus'
    )
