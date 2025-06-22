# -*- coding: utf-8 -*-
"""
基础仓库模式实现
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, desc, asc, func
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T], ABC):
    """基础仓库类"""
    
    def __init__(self, session: Session, model_class: type):
        self.session = session
        self.model_class = model_class
    
    def create(self, **kwargs) -> T:
        """创建新记录"""
        try:
            obj = self.model_class(**kwargs)
            self.session.add(obj)
            self.session.flush()
            return obj
        except SQLAlchemyError as e:
            logger.error(f"创建记录失败: {e}")
            raise
    
    def get_by_id(self, obj_id: Any) -> Optional[T]:
        """根据ID获取记录"""
        try:
            return self.session.query(self.model_class).get(obj_id)
        except SQLAlchemyError as e:
            logger.error(f"查询记录失败: {e}")
            raise
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """获取所有记录"""
        try:
            query = self.session.query(self.model_class)
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"查询所有记录失败: {e}")
            raise
    
    def update(self, obj_id: Any, **kwargs) -> Optional[T]:
        """更新记录"""
        try:
            obj = self.get_by_id(obj_id)
            if obj:
                for key, value in kwargs.items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)
                self.session.flush()
            return obj
        except SQLAlchemyError as e:
            logger.error(f"更新记录失败: {e}")
            raise
    
    def delete(self, obj_id: Any) -> bool:
        """删除记录"""
        try:
            obj = self.get_by_id(obj_id)
            if obj:
                self.session.delete(obj)
                self.session.flush()
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"删除记录失败: {e}")
            raise
    
    def count(self, **filters) -> int:
        """计算记录数量"""
        try:
            query = self.session.query(func.count(self.model_class.id))
            if filters:
                query = self._apply_filters(query, **filters)
            return query.scalar()
        except SQLAlchemyError as e:
            logger.error(f"计算记录数量失败: {e}")
            raise
    
    def exists(self, **filters) -> bool:
        """检查记录是否存在"""
        try:
            query = self.session.query(self.model_class)
            if filters:
                query = self._apply_filters(query, **filters)
            return query.first() is not None
        except SQLAlchemyError as e:
            logger.error(f"检查记录存在性失败: {e}")
            raise
    
    def paginate(self, page: int = 1, per_page: int = 20, **filters) -> Dict[str, Any]:
        """分页查询"""
        try:
            offset = (page - 1) * per_page
            
            query = self.session.query(self.model_class)
            if filters:
                query = self._apply_filters(query, **filters)
            
            total = query.count()
            items = query.offset(offset).limit(per_page).all()
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page,
                'has_prev': page > 1,
                'has_next': page * per_page < total
            }
        except SQLAlchemyError as e:
            logger.error(f"分页查询失败: {e}")
            raise
    
    def find_by(self, **filters) -> List[T]:
        """根据条件查询"""
        try:
            query = self.session.query(self.model_class)
            query = self._apply_filters(query, **filters)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"条件查询失败: {e}")
            raise
    
    def find_one_by(self, **filters) -> Optional[T]:
        """根据条件查询单个记录"""
        try:
            query = self.session.query(self.model_class)
            query = self._apply_filters(query, **filters)
            return query.first()
        except SQLAlchemyError as e:
            logger.error(f"单个记录查询失败: {e}")
            raise
    
    def _apply_filters(self, query, **filters):
        """应用过滤条件"""
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                if isinstance(value, (list, tuple)):
                    query = query.filter(getattr(self.model_class, key).in_(value))
                elif isinstance(value, dict):
                    # 支持范围查询，如 {'gte': 10, 'lte': 100}
                    column = getattr(self.model_class, key)
                    if 'gte' in value:
                        query = query.filter(column >= value['gte'])
                    if 'lte' in value:
                        query = query.filter(column <= value['lte'])
                    if 'gt' in value:
                        query = query.filter(column > value['gt'])
                    if 'lt' in value:
                        query = query.filter(column < value['lt'])
                    if 'ne' in value:
                        query = query.filter(column != value['ne'])
                    if 'like' in value:
                        query = query.filter(column.like(f"%{value['like']}%"))
                else:
                    query = query.filter(getattr(self.model_class, key) == value)
        return query
    
    def bulk_create(self, objects_data: List[Dict[str, Any]]) -> List[T]:
        """批量创建"""
        try:
            objects = [self.model_class(**data) for data in objects_data]
            self.session.add_all(objects)
            self.session.flush()
            return objects
        except SQLAlchemyError as e:
            logger.error(f"批量创建失败: {e}")
            raise
    
    def bulk_update(self, updates: List[Dict[str, Any]], id_field: str = 'id') -> int:
        """批量更新"""
        try:
            count = 0
            for update_data in updates:
                obj_id = update_data.pop(id_field)
                result = self.session.query(self.model_class).filter(
                    getattr(self.model_class, id_field) == obj_id
                ).update(update_data)
                count += result
            self.session.flush()
            return count
        except SQLAlchemyError as e:
            logger.error(f"批量更新失败: {e}")
            raise
    
    def bulk_delete(self, ids: List[Any], id_field: str = 'id') -> int:
        """批量删除"""
        try:
            count = self.session.query(self.model_class).filter(
                getattr(self.model_class, id_field).in_(ids)
            ).delete(synchronize_session=False)
            self.session.flush()
            return count
        except SQLAlchemyError as e:
            logger.error(f"批量删除失败: {e}")
            raise