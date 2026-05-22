from dataclasses import dataclass
from typing import Optional

@dataclass
class ColumnConfig:
    name: str
    role: str
    description: str
    alias: list[str]
    sync: bool

@dataclass
class TableConfig:
    name: str
    role: str
    description: str
    columns: list[ColumnConfig]

@dataclass
class MetricConfig:
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]

@dataclass
class MetaConfig:
    tables: Optional[list[TableConfig]] = None
    metrics: Optional[list[MetricConfig]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "MetaConfig":
        tables = []
        if data.get("tables"):
            for t in data["tables"]:
                columns = []
                for c in t.get("columns", []):
                    columns.append(ColumnConfig(
                        name=c["name"],
                        role=c.get("role", "dimension"),
                        description=c.get("description", ""),
                        alias=c.get("alias", []),
                        sync=c.get("sync", False)
                    ))
                tables.append(TableConfig(
                    name=t["name"],
                    role=t.get("role", "dim"),
                    description=t.get("description", ""),
                    columns=columns
                ))

        metrics = []
        if data.get("metrics"):
            for m in data["metrics"]:
                metrics.append(MetricConfig(
                    name=m["name"],
                    description=m.get("description", ""),
                    relevant_columns=m.get("relevant_columns", []),
                    alias=m.get("alias", [])
                ))

        return cls(tables=tables, metrics=metrics)

