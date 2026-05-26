import json
import uuid

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agents.viz_agent.context import VizAgentContext
from app.agents.viz_agent.graph import recommend_graph, generate_graph, dashboard_graph
from app.agents.viz_agent.state import VizAgentState
from app.entities.dashboard import Dashboard
from app.entities.dashboard_filter import DashboardFilter
from app.entities.panel import Panel
from app.repositories.es.value_es_respository import ValueEsRepository
from app.repositories.mysql.meta.datasource_repository import DatasourceRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.mysql.viz.chart_config_repository import ChartConfigRepository
from app.repositories.mysql.viz.dashboard_repository import DashboardRepository
from app.repositories.mysql.viz.panel_repository import PanelRepository
from app.repositories.mysql.viz.dashboard_filter_repository import DashboardFilterRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class VizService:
    def __init__(
        self,
        meta_mysql_repository: MetaMysqlRepository,
        datasource_repository: DatasourceRepository,
        chart_config_repository: ChartConfigRepository,
        embedding_client: HuggingFaceEndpointEmbeddings,
        column_qdrant_repository: ColumnQdrantRepository,
        value_es_repository: ValueEsRepository,
        metric_qdrant_repository: MetricQdrantRepository,
        dashboard_repository: DashboardRepository | None = None,
        panel_repository: PanelRepository | None = None,
        dashboard_filter_repository: DashboardFilterRepository | None = None,
    ):
        self.meta_mysql_repository = meta_mysql_repository
        self.datasource_repository = datasource_repository
        self.chart_config_repository = chart_config_repository
        self.embedding_client = embedding_client
        self.column_qdrant_repository = column_qdrant_repository
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.dashboard_repository = dashboard_repository
        self.panel_repository = panel_repository
        self.dashboard_filter_repository = dashboard_filter_repository

    def _build_context(self) -> VizAgentContext:
        return VizAgentContext(
            meta_mysql_repository=self.meta_mysql_repository,
            datasource_repository=self.datasource_repository,
            chart_config_repository=self.chart_config_repository,
            embedding_client=self.embedding_client,
            column_qdrant_repository=self.column_qdrant_repository,
            value_es_repository=self.value_es_repository,
            metric_qdrant_repository=self.metric_qdrant_repository,
            dashboard_repository=self.dashboard_repository,
            panel_repository=self.panel_repository,
        )

    async def recommend_chart(self, datasource_id: str, sql: str, query_result: list[dict]):
        from app.clients.datasource import datasource_manager

        if datasource_id and not datasource_manager.is_registered(datasource_id):
            datasource = await self.datasource_repository.get_by_id(datasource_id)
            if datasource:
                datasource_manager.register(datasource)

        context = self._build_context()
        state = VizAgentState(
            datasource_id=datasource_id,
            query="",
            sql=sql,
            query_result=query_result,
        )
        try:
            async for chunk in recommend_graph.astream(input=state, context=context, stream_mode="custom"):
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False, default=str)}\n\n"

    async def generate_charts(self, datasource_id: str, query: str):
        from app.clients.datasource import datasource_manager

        if datasource_id and not datasource_manager.is_registered(datasource_id):
            datasource = await self.datasource_repository.get_by_id(datasource_id)
            if datasource:
                datasource_manager.register(datasource)

        context = self._build_context()
        state = VizAgentState(
            datasource_id=datasource_id,
            query=query,
        )
        try:
            async for chunk in generate_graph.astream(input=state, context=context, stream_mode="custom"):
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False, default=str)}\n\n"

    async def generate_dashboard(self, datasource_id: str, query: str):
        from app.clients.datasource import datasource_manager

        if datasource_id and not datasource_manager.is_registered(datasource_id):
            datasource = await self.datasource_repository.get_by_id(datasource_id)
            if datasource:
                datasource_manager.register(datasource)

        context = self._build_context()
        state = VizAgentState(
            datasource_id=datasource_id,
            query=query,
        )
        try:
            async for chunk in dashboard_graph.astream(input=state, context=context, stream_mode="custom"):
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False, default=str)}\n\n"

    async def get_chart_config(self, chart_id: str):
        return await self.chart_config_repository.get_by_id(chart_id)

    async def list_charts(self, datasource_id: str, offset: int = 0, limit: int = 20):
        return await self.chart_config_repository.list_by_datasource(datasource_id, offset, limit)

    async def delete_chart(self, chart_id: str) -> bool:
        return await self.chart_config_repository.delete(chart_id)

    # ================ Dashboard ================

    async def create_dashboard(self, data: dict) -> Dashboard:
        dashboard = Dashboard(
            id=str(uuid.uuid4()),
            name=data["name"],
            description=data.get("description"),
            datasource_id=data.get("datasource_id"),
            theme=data.get("theme", "dark"),
            theme_config=data.get("theme_config"),
            layout_config=data.get("layout_config", {"cols": 12, "row_height": 100, "gap": 12}),
            refresh_enabled=data.get("refresh_enabled", False),
            refresh_interval=data.get("refresh_interval", 60),
        )
        return await self.dashboard_repository.create(dashboard)

    async def get_dashboard(self, dashboard_id: str):
        dashboard = await self.dashboard_repository.get_by_id(dashboard_id)
        if dashboard is None:
            return None
        panels = await self.panel_repository.list_by_dashboard(dashboard_id)
        filters = await self.dashboard_filter_repository.list_by_dashboard(dashboard_id)
        return {
            "dashboard": dashboard,
            "panels": panels,
            "filters": filters,
        }

    async def update_dashboard(self, dashboard_id: str, data: dict) -> Dashboard | None:
        dashboard = await self.dashboard_repository.get_by_id(dashboard_id)
        if dashboard is None:
            return None
        for key, value in data.items():
            if value is not None and hasattr(dashboard, key):
                setattr(dashboard, key, value)
        return await self.dashboard_repository.update(dashboard)

    async def delete_dashboard(self, dashboard_id: str) -> bool:
        dashboard = await self.dashboard_repository.get_by_id(dashboard_id)
        if dashboard is None:
            return False
        await self.dashboard_filter_repository.delete_by_dashboard(dashboard_id)
        await self.panel_repository.delete_by_dashboard(dashboard_id)
        return await self.dashboard_repository.delete(dashboard_id)

    async def list_dashboards(self, offset: int = 0, limit: int = 20, status: str | None = None):
        items = await self.dashboard_repository.list_all(offset, limit, status)
        total = await self.dashboard_repository.count_all(status)
        return {"total": total, "items": items}

    # ================ Panel ================

    async def add_panel(self, dashboard_id: str, data: dict) -> Panel | None:
        dashboard = await self.dashboard_repository.get_by_id(dashboard_id)
        if dashboard is None:
            return None
        if "chart_config_id" in data and data["chart_config_id"]:
            chart = await self.chart_config_repository.get_by_id(data["chart_config_id"])
            if chart is None:
                return None
            if data.get("title") is None:
                data["title"] = chart.name
        panel = Panel(
            id=str(uuid.uuid4()),
            dashboard_id=dashboard_id,
            chart_config_id=data.get("chart_config_id"),
            title=data.get("title"),
            layout_x=data.get("layout_x", 0),
            layout_y=data.get("layout_y", 0),
            layout_w=data.get("layout_w", 6),
            layout_h=data.get("layout_h", 4),
            sort_order=data.get("sort_order", 0),
        )
        return await self.panel_repository.create(panel)

    async def update_panel(self, panel_id: str, data: dict) -> Panel | None:
        panel = await self.panel_repository.get_by_id(panel_id)
        if panel is None:
            return None
        for key, value in data.items():
            if value is not None and hasattr(panel, key):
                setattr(panel, key, value)
        return await self.panel_repository.update(panel)

    async def delete_panel(self, panel_id: str) -> bool:
        return await self.panel_repository.delete(panel_id)

    async def batch_reorder_panels(self, panels_data: list[dict]) -> None:
        panels = []
        for item in panels_data:
            panel = await self.panel_repository.get_by_id(item["id"])
            if panel is None:
                continue
            for key, value in item.items():
                if value is not None and hasattr(panel, key):
                    setattr(panel, key, value)
            panels.append(panel)
        await self.panel_repository.batch_update_layout(panels)

    # ================ DashboardFilter ================

    async def add_filter(self, dashboard_id: str, data: dict) -> DashboardFilter | None:
        dashboard = await self.dashboard_repository.get_by_id(dashboard_id)
        if dashboard is None:
            return None
        dashboard_filter = DashboardFilter(
            id=str(uuid.uuid4()),
            dashboard_id=dashboard_id,
            name=data["name"],
            label=data["label"],
            filter_type=data["filter_type"],
            config=data.get("config", {}),
            target_panels=data.get("target_panels"),
            sort_order=data.get("sort_order", 0),
        )
        return await self.dashboard_filter_repository.create(dashboard_filter)

    async def update_filter(self, filter_id: str, data: dict) -> DashboardFilter | None:
        dashboard_filter = await self.dashboard_filter_repository.get_by_id(filter_id)
        if dashboard_filter is None:
            return None
        for key, value in data.items():
            if value is not None and hasattr(dashboard_filter, key):
                setattr(dashboard_filter, key, value)
        return await self.dashboard_filter_repository.update(dashboard_filter)

    async def delete_filter(self, filter_id: str) -> bool:
        return await self.dashboard_filter_repository.delete(filter_id)

    async def get_filters(self, dashboard_id: str) -> list[DashboardFilter]:
        return await self.dashboard_filter_repository.list_by_dashboard(dashboard_id)