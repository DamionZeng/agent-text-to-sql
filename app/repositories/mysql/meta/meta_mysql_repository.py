from sqlalchemy import text, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.models.column_info import ColumnInfoMySQL
from app.models.table_info import TableInfoMySQL
from app.models.metric_info import MetricInfoMySQL
from app.models.column_metric import ColumnMetricMySQL
from app.repositories.mysql.meta.mappers.column_info_mapper import ColumnInfoMapper
from app.repositories.mysql.meta.mappers.column_metric_mapper import ColumnMetricMapper
from app.repositories.mysql.meta.mappers.metric_info_mapper import MetricInfoMapper
from app.repositories.mysql.meta.mappers.table_info_mapper import TableInfoMapper


class MetaMysqlRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    def read(self):
        pass

    def write(self):
        pass

    def save_table_infos(self, table_infos: list[TableInfo]):
        self.session.add_all([TableInfoMapper.to_model(table_info) for table_info in table_infos])

    def save_column_infos(self, column_infos: list[ColumnInfo]):
        self.session.add_all([ColumnInfoMapper.to_model(column_info) for column_info in column_infos])

    def save_metric_infos(self, metric_infos: list[MetricInfo]):
        self.session.add_all([MetricInfoMapper.to_model(metric_info) for metric_info in metric_infos])

    def save_column_metrics(self, column_metrics: list[ColumnMetric]):
        self.session.add_all([ColumnMetricMapper.to_model(column_metric) for column_metric in column_metrics])

    async def delete_table_infos(self, table_ids: list[str]):
        await self.session.execute(delete(TableInfoMySQL).where(TableInfoMySQL.id.in_(table_ids)))

    async def delete_column_infos_by_table_ids(self, table_ids: list[str]):
        await self.session.execute(delete(ColumnInfoMySQL).where(ColumnInfoMySQL.table_id.in_(table_ids)))

    async def delete_metric_infos(self, metric_ids: list[str]):
        await self.session.execute(delete(MetricInfoMySQL).where(MetricInfoMySQL.id.in_(metric_ids)))

    async def delete_column_metrics_by_metric_ids(self, metric_ids: list[str]):
        await self.session.execute(delete(ColumnMetricMySQL).where(ColumnMetricMySQL.metric_id.in_(metric_ids)))

    async def get_column_info_by_id(self, id: str) -> ColumnInfo | None:
        column_info_mysql:ColumnInfoMySQL | None = await self.session.get(ColumnInfoMySQL, id)
        if column_info_mysql:
            return ColumnInfoMapper.to_entity(column_info_mysql)
        else:
            return None

    async def get_table_info_by_id(self, id: str) -> TableInfo | None:
        table_info_mysql: TableInfoMySQL | None = await self.session.get(TableInfoMySQL, id)
        if table_info_mysql:
            return TableInfoMapper.to_entity(table_info_mysql)
        else:
            return None

    async def get_key_columns_by_table_id(self, table_id: str) -> list[ColumnInfo]:
        sql = f"select * from column_info where table_id='{table_id}' and role in ('primary_key', 'foreign_key')"
        result = await self.session.execute(text(sql))
        return [ColumnInfo(**dict(row)) for row in result.mappings().fetchall()]

