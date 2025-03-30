import uuid
from typing import List, TypeVar, Generic, Type, Optional, cast, Any
from pydantic import BaseModel
import logging

from sqlalchemy import Select
from sqlmodel import SQLModel, Session, select, update, delete, func, col


T = TypeVar("T", bound=SQLModel)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BaseDAO(Generic[T]):
    model: Type[T] = None

    def __init__(self, session: Session):
        self._session = session
        if self.model is None:
            raise ValueError("Model must be specified in the child class")


    def find_one_or_none_by_id(self, data_id: uuid.UUID | str) -> Optional[T]:
        """Find a record by its ID."""
        try:
            query = cast(Select[T], select(self.model).where(self.model.id == data_id))
            return self._session.exec(query).first()
        except Exception as e:
            logger.error(f"Error finding record by ID {data_id}: {str(e)}")
            raise

    def find_one_or_none(self, filters: dict) -> Optional[T]:
        """Find a single record matching the filters."""
        try:
            query = select(self.model)
            for field, value in filters.items():
                query = query.where(getattr(self.model, field) == value)
            return self._session.exec(query).first()
        except Exception as e:
            logger.error(f"Error finding record with filters: {str(e)}")
            raise

    def add(self, values: BaseModel) -> T:
        """Add a new record."""
        try:
            values_dict = values.model_dump(exclude_unset=True)
            new_instance = self.model(**values_dict)
            self._session.add(new_instance)
            self._session.flush()
            self._session.refresh(new_instance)
            return new_instance
        except Exception as e:
            self._session.rollback()
            logger.error(f"Error adding record: {str(e)}")
            raise

    def add_many(self, instances: List[BaseModel]) -> List[T]:
        """Bulk insert multiple records."""
        try:
            values_list = [item.model_dump(exclude_unset=True) for item in instances]
            new_instances = [self.model(**inst) for inst in values_list]
            self._session.add_all(new_instances)
            self._session.flush()
            return new_instances
        except Exception as e:
            self._session.rollback()
            logger.error(f"Error adding multiple records: {str(e)}")
            raise

    def find_all(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[T]:
        """Get all records matching optional filters."""
        try:
            query = select(self.model)
            if filters:
                for field, value in filters.items():
                    if value is not None:  # Skip None values
                        query = query.where(getattr(self.model, field) == value)

            query = query.offset(skip).limit(limit)

            result = self._session.exec(query)
            return list(result.all())

        except Exception as e:
            logger.error(f"Error fetching records (skip={skip}, limit={limit}): {str(e)}")
            raise

    def update(self, filters: dict, values: BaseModel | dict[str, Any]) -> T:
        """Update records matching filters and return updated entity"""
        try:
            values_dict = values.model_dump(exclude_unset=True) if isinstance(values, BaseModel) else values

            entity = self.find_one_or_none(filters)
            if not entity:
                raise ValueError("Record not found")

            for field, value in values_dict.items():
                setattr(entity, field, value)

            self._session.add(entity)
            self._session.flush()
            self._session.refresh(entity)
            return entity

        except Exception as e:
            self._session.rollback()
            logger.error(f"Error updating record: {str(e)}")
            raise

    def delete(self, filters: dict = None) -> int:
        """Delete records matching filters."""
        try:

            if not filters:
                raise ValueError("At least one filter is required for deletion")

            stmt = delete(self.model)
            for field, value in filters.items():
                stmt = stmt.where(getattr(self.model, field) == value)

            result = self._session.exec(stmt)
            self._session.flush()

            # Get the number of affected rows
            return result.rowcount if hasattr(result, 'rowcount') else 0
        except Exception as e:
            self._session.rollback()
            logger.error(f"Error deleting records: {str(e)}")
            raise

    def count(self, filters: Optional[BaseModel] = None) -> int:
        """Count records matching optional filters."""
        try:
            query = select(func.count()).select_from(self.model)
            if filters:
                filter_dict = filters.model_dump(exclude_unset=True)
                for field, value in filter_dict.items():
                    query = query.where(col(getattr(self.model, field)) == value)
            return self._session.exec(query).scalar()
        except Exception as e:
            logger.error(f"Error counting records: {str(e)}")
            raise