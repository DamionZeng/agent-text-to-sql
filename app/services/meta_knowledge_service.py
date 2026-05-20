import uuid
from dataclasses import asdict
from pathlib import Path

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from omegaconf import OmegaConf
from app.conf.meta_config import MetaConfig
from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.entities.value_info import ValueInfo
from app.repositories.es.value_es_respository import ValueEsRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.core.log import logger

class MetaKnowledgeService:
    def __init__(self,
                 meta_mysql_repository: MetaMysqlRepository,
                 dw_mysql_repository: DWMysqlRepository,
                 column_qdrant_repository: ColumnQdrantRepository,
                 embedding_client: HuggingFaceEndpointEmbeddings,
                 value_es_repository: ValueEsRepository,
                 metric_qdrant_repository: MetricQdrantRepository,
                 ):
        self.meta_mysql_repository: MetaMysqlRepository = meta_mysql_repository
        self.dw_mysql_repository: DWMysqlRepository = dw_mysql_repository
        self.column_qdrant_repository: ColumnQdrantRepository = column_qdrant_repository
        self.embedding_client: HuggingFaceEndpointEmbeddings = embedding_client
        self.value_es_repository: ValueEsRepository = value_es_repository
        self.metric_qdrant_repository: MetricQdrantRepository = metric_qdrant_repository

    async def _save_tables_to_meta_db(self, meta_config: MetaConfig, datasource_prefix: str = "", datasource_id: str = "") -> list[ColumnInfo]:
        table_infos: list[TableInfo] = []
        column_infos: list[ColumnInfo] = []
        for table in meta_config.tables:
            table_id = f"{datasource_prefix}{table.name}"
            table_info = TableInfo(
                id=table_id,
                name=table.name,
                role=table.role,
                description=table.description,
                alias=getattr(table, 'alias', []),
                datasource_id=datasource_id,
            )
            table_infos.append(table_info)
            column_types = await self.dw_mysql_repository.get_column_type(table.name)

            for column in table.columns:
                column_values = await self.dw_mysql_repository.get_column_value(table.name, column.name)

                column_info = ColumnInfo(
                    id=f"{table_id}.{column.name}",
                    name=column.name,
                    type=column_types[column.name],
                    role=column.role,
                    examples=column_values,
                    description=column.description,
                    alias=column.alias,
                    table_id=table_id,
                    is_sync=column.sync
                )
                column_infos.append(column_info)
        
        table_ids = [t.id for t in table_infos]
        if table_ids:
            await self.meta_mysql_repository.delete_table_infos(table_ids)
            await self.meta_mysql_repository.delete_column_infos_by_table_ids(table_ids)
        
        await self.meta_mysql_repository.save_table_infos(table_infos)
        await self.meta_mysql_repository.save_column_infos(column_infos)
        return column_infos

    async def _save_columns_to_qdrant(self, column_infos: list[ColumnInfo]):
        await self.column_qdrant_repository.ensure_collection()

        points: list[dict] = []
        for column_info in column_infos:
            points.append({
                'id': uuid.uuid4(),
                'embedding_text': column_info.name,
                'payload': asdict(column_info)
            })
            # 别名向量化
            for alia in column_info.alias:
                points.append({
                    'id': uuid.uuid4(),
                    'embedding_text': alia,
                    'payload': asdict(column_info)
                })
        # 批量向量化
        embeddings: list[list[float]] = []
        embedding_texts = [point['embedding_text'] for point in points]
        embedding_size = 10
        for i in range(0, len(embedding_texts), embedding_size):
            batch_embedding = await self.embedding_client.aembed_documents(embedding_texts[i:i + embedding_size])
            embeddings.extend(batch_embedding)

        ids = [point['id'] for point in points]
        payloads = [point['payload'] for point in points]

        await self.column_qdrant_repository.upsert(ids, embeddings, payloads)

    async def _save_values_to_es(self, meta_config: MetaConfig, datasource_prefix: str = ""):
        await self.value_es_repository.ensure_index()
        value_infos: list[ValueInfo] = []
        for table in meta_config.tables:
            table_id = f"{datasource_prefix}{table.name}"
            for column in table.columns:
                if column.sync:
                    current_column_values = await self.dw_mysql_repository.get_column_value(table.name, column.name,
                                                                                            100000)
                    current_value_infos = [ValueInfo(
                        id=f"{table_id}.{column.name}.{current_column_value}",
                        value=current_column_value,
                        column_id=f"{table_id}.{column.name}"
                    ) for current_column_value in current_column_values]
                    value_infos.extend(current_value_infos)
        await self.value_es_repository.index(value_infos)

    async def _save_metrics_to_meta_db(self, meta_config: MetaConfig, datasource_prefix: str = "")-> list[MetricInfo]:
        metric_infos: list[MetricInfo] = []
        column_metrics: list[ColumnMetric] = []

        for metric in meta_config.metrics:
            metric_id = f"{datasource_prefix}{metric.name}"
            relevant_columns_with_prefix = [f"{datasource_prefix}{col}" for col in metric.relevant_columns]
            metric_info = MetricInfo(
                id=metric_id,
                name=metric.name,
                description=metric.description,
                relevant_columns=relevant_columns_with_prefix,
                alias=metric.alias
            )
            metric_infos.append(metric_info)
            for column in metric.relevant_columns:
                column_metric = ColumnMetric(
                    metric_id=metric_id,
                    column_id=f"{datasource_prefix}{column}"
                )
                column_metrics.append(column_metric)
        
        metric_ids = [m.id for m in metric_infos]
        if metric_ids:
            await self.meta_mysql_repository.delete_metric_infos(metric_ids)
            await self.meta_mysql_repository.delete_column_metrics_by_metric_ids(metric_ids)
        
        await self.meta_mysql_repository.save_metric_infos(metric_infos)
        await self.meta_mysql_repository.save_column_metrics(column_metrics)
        return metric_infos

    async def _save_metrics_to_qdrant(self, metric_infos: list[MetricInfo]):
        await self.metric_qdrant_repository.ensure_collection()

        points: list[dict] = []
        for metric_info in metric_infos:
            points.append({
                'id': uuid.uuid4(),
                'embedding_text': metric_info.name,
                'payload': asdict(metric_info)
            })
            # 别名向量化
            for alia in metric_info.alias:
                points.append({
                    'id': uuid.uuid4(),
                    'embedding_text': alia,
                    'payload': asdict(metric_info)
                })
        # 批量向量化
        embeddings: list[list[float]] = []
        embedding_texts = [point['embedding_text'] for point in points]
        embedding_size = 10
        for i in range(0, len(embedding_texts), embedding_size):
            batch_embedding = await self.embedding_client.aembed_documents(embedding_texts[i:i + embedding_size])
            embeddings.extend(batch_embedding)

        ids = [point['id'] for point in points]
        payloads = [point['payload'] for point in points]

        await self.metric_qdrant_repository.upsert(ids, embeddings, payloads)

    async def build(self, config_path: Path):
        # 1. 读取配置文件
        context = OmegaConf.load(config_path)
        schema = OmegaConf.structured(MetaConfig)
        meta_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(schema,context))
        logger.info("加载配置文件成功")
        # 2. 根据配置文件同步指定的表信息和指标信息
        if meta_config.tables:
            # 2.1 表信息同步
            column_infos = await self._save_tables_to_meta_db(meta_config, "", "")
            logger.info("保存表信息和字段信息到数据库成功")

            # 2.2 对字段信息建立向量索引
            await self._save_columns_to_qdrant(column_infos)
            logger.info("字段信息向量索引success")

            # 2.3 对指定维度字段取值建立全文索引
            await self._save_values_to_es(meta_config, "")
            logger.info("全文索引success")

        # 3. 根据配置文件同步指定的指标信息
        if meta_config.metrics:
            # 3.1 将指标信息保存meta数据库中
            metric_infos = await self._save_metrics_to_meta_db(meta_config, "")
            logger.info("指标信息入库成功")

            # 3.2 对指标信息建立向量索引
            await self._save_metrics_to_qdrant(metric_infos)
            logger.info("指标信息向量化成功")

    async def build_from_config(self, meta_config: MetaConfig, datasource_prefix: str = "", datasource_id: str = ""):
        """直接从 MetaConfig 对象构建知识库（无需配置文件）
        
        Args:
            meta_config: 元数据配置
            datasource_prefix: 数据源前缀，格式为 "{type}_{name}_"，用于生成唯一ID
            datasource_id: 数据源ID
        """
        logger.info("开始从配置对象构建知识库")
        if meta_config.tables:
            column_infos = await self._save_tables_to_meta_db(meta_config, datasource_prefix, datasource_id)
            logger.info("保存表信息和字段信息到数据库成功")
            await self._save_columns_to_qdrant(column_infos)
            logger.info("字段信息向量索引success")
            await self._save_values_to_es(meta_config, datasource_prefix)
            logger.info("全文索引success")
        if meta_config.metrics:
            metric_infos = await self._save_metrics_to_meta_db(meta_config, datasource_prefix)
            logger.info("指标信息入库成功")
            await self._save_metrics_to_qdrant(metric_infos)
            logger.info("指标信息向量化成功")
        logger.info("知识库构建完成")


