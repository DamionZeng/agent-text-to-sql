from app.entities.dataset import Dataset
from app.entities.dataset_field import DatasetField
from app.models.dataset import DatasetMySQL, DatasetFieldMySQL

class DatasetMapper:
    @staticmethod
    def to_model(entity: Dataset) -> DatasetMySQL:
        return DatasetMySQL(
            id=entity.id,
            name=entity.name,
            datasource_id=entity.datasource_id,
            group_id=entity.group_id,
            type=entity.type,
            info=entity.info,
            description=entity.description,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    @staticmethod
    def to_entity(model: DatasetMySQL) -> Dataset:
        return Dataset(
            id=model.id,
            name=model.name,
            datasource_id=model.datasource_id,
            group_id=model.group_id,
            type=model.type,
            info=model.info,
            description=model.description,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

class DatasetFieldMapper:
    @staticmethod
    def to_model(entity: DatasetField) -> DatasetFieldMySQL:
        return DatasetFieldMySQL(
            id=entity.id,
            dataset_id=entity.dataset_id,
            origin_name=entity.origin_name,
            name=entity.name,
            data_type=entity.data_type,
            role=entity.role,
            ext_field=entity.ext_field,
            expression=entity.expression,
            checked=entity.checked,
            sort_order=entity.sort_order,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    @staticmethod
    def to_entity(model: DatasetFieldMySQL) -> DatasetField:
        return DatasetField(
            id=model.id,
            dataset_id=model.dataset_id,
            origin_name=model.origin_name,
            name=model.name,
            data_type=model.data_type,
            role=model.role,
            ext_field=model.ext_field,
            expression=model.expression,
            checked=model.checked,
            sort_order=model.sort_order,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
