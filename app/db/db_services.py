from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.future import select
from sqlalchemy import insert

from logger import logger

from utils import (
    DATA_FIELD,
    FIELD_NOT_FOUND_IN_MODEL,
    INVALID_FIELDS,
    NOT_FOUND,
    STATUS_ERROR,
    STATUS_FIELD,
)

from utils import (
    create_service_failure_response,
    create_service_success_response,
)

Model = TypeVar("Model", bound=DeclarativeMeta)
Schema = TypeVar("Schema", bound=BaseModel)
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)



class DBRecordService:
    @staticmethod
    async def fetch_records(
        db: AsyncSession,
        model: type[Model],
        schema: type[Schema],
        filters: dict[str, Any] | None = None,
        custom_filters: list[Any] | None = None,
    ) -> dict[str, str | list[Schema]]:
        try:
            stmt = select(model)
            if filters:
                for field, value in filters.items():
                    if "__in" in field:
                        column_name = field.split("__")[0]
                        column_attr = getattr(model, column_name, None)

                        if column_attr is not None and isinstance(value, list):
                            stmt = stmt.where(column_attr.in_(value))
                        else:
                            logger.warning(
                                "Field not found",
                                field=field,
                                error=FIELD_NOT_FOUND_IN_MODEL,
                                table_name=model.__table__,
                            )
                    else:
                        column_attr = getattr(model, field, None)
                        if column_attr is not None:
                            stmt = stmt.where(column_attr == value)
                        else:
                            logger.warning(
                                "Field not found",
                                field=field,
                                error=FIELD_NOT_FOUND_IN_MODEL,
                                table_name=model.__table__,
                            )
            if custom_filters:
                for condition in custom_filters:
                    stmt = stmt.where(condition)
            result = await db.execute(stmt)
            record_models = result.scalars().all()
            data = [
                schema.model_validate(record, from_attributes=True)
                for record in record_models
            ]
            return create_service_success_response(data)
        except Exception as e:
            return create_service_failure_response(str(e))

    @staticmethod
    async def create_record(
        db: AsyncSession,
        model: type[Model],
        schema: type[Schema],
        create_data: CreateSchema,
    ) -> dict[str, str | Schema]:
        try:
            create_data_dict = create_data.model_dump()
            valid_fields = {}
            invalid_fields = []
            for key, value in create_data_dict.items():
                if hasattr(model, key):
                    valid_fields[key] = value
                else:
                    invalid_fields.append(key)
            if invalid_fields:
                logger.warning(
                    "Invalid Fields",
                    error=INVALID_FIELDS,
                    invalid_fields=invalid_fields,
                )
            entity_model = model(**valid_fields)
            db.add(entity_model)
            await db.commit()
            await db.refresh(entity_model)
            return create_service_success_response(schema.model_validate(entity_model))
        except Exception as e:
            await db.rollback()
            return create_service_failure_response(str(e))
    
    @staticmethod
    async def bulk_create_records(
        db: AsyncSession,
        model,
        records: list[dict],
        batch_size: int = 1000,
    ) -> dict:
        try:
            total_inserted = 0

            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]

                await db.execute(
                    insert(model).values(batch)
                )

                await db.commit()

                total_inserted += len(batch)
                
                logger.info(f"Total inserted {total_inserted + len(batch)}")

            return create_service_success_response(
                {
                    "inserted_count": total_inserted,
                }
            )

        except Exception as e:
            await db.rollback()
            return create_service_failure_response(str(e))

    @staticmethod
    async def update_record(
        db: AsyncSession,
        model: type[Model],
        schema: type[Schema],
        record_id: UUID | int,
        update_data: UpdateSchema,
    ) -> dict[str, str | Schema]:
        try:
            result = await db.execute(select(model).where(model.id == record_id))
            data_model = result.scalars().first()
            if not data_model:
                return create_service_failure_response(
                    f"{schema.__name__.upper()} {NOT_FOUND}"
                )
            data_dict = update_data.model_dump(exclude_none=True)
            for field, value in data_dict.items():
                if hasattr(data_model, field):
                    setattr(data_model, field, value)

            await db.commit()
            await db.refresh(data_model)
            return create_service_success_response(schema.model_validate(data_model))
        except Exception as e:
            await db.rollback()
            return create_service_failure_response(str(e))

    @staticmethod
    async def get_record_by_id(
        db: AsyncSession,
        model: type[Model],
        schema: type[Schema],
        record_id: UUID | int,
    ) -> dict[str, str | Schema]:
        try:
            result = await db.execute(select(model).where(model.id == record_id))
            record_model = result.scalars().first()
            if not record_model:
                return create_service_failure_response(
                    f"{schema.__name__.upper()} {NOT_FOUND}"
                )
            return create_service_success_response(schema.model_validate(record_model))
        except Exception as e:
            return create_service_failure_response(str(e))

    @staticmethod
    async def get_records(
        db: AsyncSession,
        model: type[Model],
        schema: type[Schema],
        params: dict[str, Any] | None = None,
        custom_filters: list[Any] | None = None,
    ) -> dict[str, str | list[Schema]]:
        return await DBRecordService.fetch_records(
            db=db,
            model=model,
            schema=schema,
            filters=params,
            custom_filters=custom_filters,
        )

    @staticmethod
    async def get_one_record_by_params(
        db: AsyncSession,
        model: type[Model],
        schema: type[Schema],
        params: dict[str, Any],
    ) -> dict[str, str | Schema]:
        response = await DBRecordService.fetch_records(
            db=db, model=model, schema=schema, filters=params
        )
        if response[STATUS_FIELD] == STATUS_ERROR:
            return response
        if len(response[DATA_FIELD]) == 0:
            return create_service_failure_response(
                f"{schema.__name__.upper()} {NOT_FOUND}"
            )
        response[DATA_FIELD] = response[DATA_FIELD][0]
        return response

    @staticmethod
    async def is_record_exists(
        db: AsyncSession,
        model: type[Model],
        schema: type[Schema],
        params: dict[str, Any],
    ) -> dict[str, str | bool]:
        response = await DBRecordService.fetch_records(
            db=db, model=model, schema=schema, filters=params
        )
        if response[STATUS_FIELD] == STATUS_ERROR:
            return response
        if len(response[DATA_FIELD]) == 0:
            return create_service_success_response(False)
        return create_service_success_response(True)
