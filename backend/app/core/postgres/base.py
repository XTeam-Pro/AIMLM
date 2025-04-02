import uuid
from typing import List, TypeVar, Generic, Type, Optional, Dict, Any, Union
from pydantic import BaseModel
import logging
from sqlmodel import SQLModel, Session, select, delete, func, and_


T = TypeVar("T", bound=SQLModel)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BaseDAO(Generic[T]):
    model: Type[T] = None

    def __init__(self, session: Session):
        self._session = session
        if self.model is None:
            raise ValueError("Model must be specified in the child class")

    def _validate_fields(self, filters: Dict[str, Any]) -> None:
        """Model field name validation (SQL injection protection)"""
        valid_fields = self.model.model_fields.keys()
        for field in filters.keys():
            if field not in valid_fields:
                raise ValueError(f"Invalid field name: '{field}'")

    def find_one_or_none_by_id(self, data_id: uuid.UUID | str) -> Optional[T]:
        """Find a record by its ID using SQLModel methods."""
        try:
            statement = select(self.model).where(self.model.id == data_id)
            result = self._session.execute(statement).first()
            return result
        except Exception as e:
            logger.error(f"Error finding record by ID {data_id}: {str(e)}")
            self._session.rollback()
            raise

    def find_one_or_none(self, filters: Dict[str, Any]) -> Optional[T]:
        try:
            self._validate_fields(filters)
            statement = select(self.model)
            conditions = [getattr(self.model, field) == value for field, value in filters.items()]
            if conditions:
                statement = statement.where(and_(*conditions))
            # Use scalars() to get model instances instead of Row objects
            return self._session.scalars(statement).first()
        except Exception as e:
            logger.error(f"Error finding record with filters {filters}: {str(e)}")
            self._session.rollback()
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

            # Refresh all instances
            for instance in new_instances:
                self._session.refresh(instance)

            return new_instances
        except Exception as e:
            self._session.rollback()
            logger.error(f"Error adding multiple records: {str(e)}")
            raise

    def find_all(
            self,
            skip: int = 0,
            limit: int = 100,
            filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get all records matching optional filters."""
        try:
            if limit > 1000:
                raise ValueError("Limit cannot exceed 1000")

            statement = select(self.model)

            if filters:
                self._validate_fields(filters)
                conditions = []
                for field, value in filters.items():
                    if value is not None:
                        conditions.append(getattr(self.model, field) == value)

                if conditions:
                    statement = statement.where(and_(*conditions))

            statement = statement.offset(skip).limit(limit)
            result = self._session.execute(statement)
            return list(result.all())
        except Exception as e:
            logger.error(f"Error fetching records: {str(e)}")
            self._session.rollback()
            raise

    def update(
            self,
            filters: Dict[str, Any],
            values: Union[BaseModel, Dict[str, Any]]
    ) -> T:
        """Update records matching filters and return updated entity"""
        try:
            self._validate_fields(filters)

            values_dict = values.model_dump(exclude_unset=True) if isinstance(values, BaseModel) else values
            self._validate_fields(values_dict)

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

    def delete(self, filters: Union[BaseModel, Dict[str, Any]]) -> int:
        """Delete records matching filters."""
        try:
            if isinstance(filters, BaseModel):
                filters = filters.model_dump(exclude_unset=True)
            elif not isinstance(filters, dict):
                raise ValueError("Filters must be a dict or BaseModel")

            if not filters:
                raise ValueError("At least one filter is required for deletion")

            self._validate_fields(filters)
            conditions = []
            for field, value in filters.items():
                conditions.append(getattr(self.model, field) == value)

            statement = delete(self.model).where(and_(*conditions))
            result = self._session.execute(statement)
            self._session.flush()
            return result.rowcount
        except Exception as e:
            self._session.rollback()
            logger.error(f"Delete error: {str(e)}")
            raise

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records matching optional filters."""
        try:
            statement = select(func.count()).select_from(self.model)

            if filters:
                self._validate_fields(filters)
                conditions = []
                for field, value in filters.items():
                    conditions.append(getattr(self.model, field) == value)

                if conditions:
                    statement = statement.where(and_(*conditions))

            return self._session.execute(statement).one()
        except Exception as e:
            logger.error(f"Error counting records: {str(e)}")
            self._session.rollback()
            raise