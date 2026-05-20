from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, TableInfoState, MetricInfoState, ColumnInfoState
from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.entities.value_info import ValueInfo
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.core.log import logger


async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "合并关键信息", "status": "running"})
    try:
        retrieved_column_infos: list[ColumnInfo] = state['retrieved_column_infos']
        retrieved_value_infos: list[ValueInfo] = state['retrieved_value_infos']
        retrieved_metric_infos: list[MetricInfo] = state['retrieved_metric_infos']


        meta_mysql_repository: MetaMysqlRepository = runtime.context['meta_mysql_repository']

        # 处理表信息
        retrieved_column_infos_map: dict[str, ColumnInfo] = {retrieved_column_info.id:retrieved_column_info for
                                                             retrieved_column_info in retrieved_column_infos}
        
        print(retrieved_column_infos_map)
        # 指标相关字段加入字段信息中
        for retrieved_metric_info in retrieved_metric_infos:
            for relevant_column in retrieved_metric_info.relevant_columns:
                if relevant_column not in retrieved_column_infos_map:
                    column_info: ColumnInfo = await meta_mysql_repository.get_column_info_by_id(relevant_column)
                    retrieved_column_infos_map[relevant_column] = column_info
        # 字段值加入其所属字段的examples
        for retrieved_value_info in retrieved_value_infos:
            value = retrieved_value_info.value
            column_id = retrieved_value_info.column_id
            if column_id not in retrieved_column_infos_map:
                column_info: ColumnInfo = await meta_mysql_repository.get_column_info_by_id(column_id)
                retrieved_column_infos_map[column_id] = column_info
            if value not in retrieved_column_infos_map[column_id].examples:
                retrieved_column_infos_map[column_id].examples.append(value)

        # 按照表对字段信息进行分组
        table_to_columns_map: dict[str, list[ColumnInfo]] = {}
        for column_info in retrieved_column_infos_map.values():
            table_id = column_info.table_id
            if table_id not in table_to_columns_map:
                table_to_columns_map[table_id] = []
            table_to_columns_map[table_id].append(column_info)
        # 强制为每个表添加主外字段
        for table_id in table_to_columns_map.keys():
            key_columns: list[ColumnInfo] = await meta_mysql_repository.get_key_columns_by_table_id(table_id)
            column_ids = [column_info.id for column_info in table_to_columns_map[table_id]]
            for key_column in key_columns:
                if key_column.id not in column_ids:
                    table_to_columns_map[table_id].append(key_column)

        # 将表信息整理成目标格式
        table_infos_state: list[TableInfoState] = []
        for table_id, column_infos in table_to_columns_map.items():
            table_info:TableInfo = await meta_mysql_repository.get_table_info_by_id(table_id)
            column_infos_state = [ColumnInfoState(
                name= column_info.name,
                type=column_info.type,
                role=column_info.role,
                examples=column_info.examples,
                description=column_info.description,
                alias=column_info.alias,
            ) for column_info in column_infos]
            table_info_state = TableInfoState(
                name=table_info.name,
                role=table_info.role,
                description=table_info.description,
                columns=column_infos_state
            )
            table_infos_state.append(table_info_state)

        # 处理指标信息
        # metric_infos = list[MetricInfoState]
        metric_infos_state: list[MetricInfoState] = [MetricInfoState(
            name=retrieved_metric_info.name,
            description=retrieved_metric_info.description,
            relevant_columns=retrieved_metric_info.relevant_columns,
            alias=retrieved_metric_info.alias,
        ) for retrieved_metric_info in retrieved_metric_infos]
        table_names = [table_info_state['name'] for table_info_state in table_infos_state]
        metric_names = [metric_info_state['name'] for metric_info_state in metric_infos_state]
        logger.info(f"合并后的表名: {table_names}, 指标: {metric_names}")
        writer({"type": "progress", "step": "合并关键信息", "status": "success"})
        return {
            "table_infos": table_infos_state,
            "metric_infos": metric_infos_state,
        }
    except Exception as e:
        logger.error(f"合并关键信息失败: {str(e)}")
        writer({"type": "progress", "step": "合并关键信息", "status": "error"})
        raise e
