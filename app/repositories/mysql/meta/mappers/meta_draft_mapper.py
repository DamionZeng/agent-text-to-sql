from dataclasses import asdict

from app.entities.meta_draft import MetaDraft
from app.models.meta_draft import MetaDraftMySQL


class MetaDraftMapper:
    @staticmethod
    def to_entity(meta_draft_mysql: MetaDraftMySQL) -> MetaDraft:
        return MetaDraft(
            id=meta_draft_mysql.id,
            datasource_id=meta_draft_mysql.datasource_id,
            config_json=meta_draft_mysql.config_json,
            version=meta_draft_mysql.version,
            status=meta_draft_mysql.status,
            created_at=meta_draft_mysql.created_at,
            updated_at=meta_draft_mysql.updated_at,
        )

    @staticmethod
    def to_model(meta_draft: MetaDraft) -> MetaDraftMySQL:
        return MetaDraftMySQL(**asdict(meta_draft))