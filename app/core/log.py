import sys
from pathlib import Path

from loguru import logger

from app.conf.app_config import conf
from app.core.context import request_id_ctx_var

log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<magenta>request_id - {extra[request_id]}</magenta> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# 注入request_id到日志记录中
def inject_request_id(record):
    request_id = request_id_ctx_var.get()
    record["extra"]["request_id"] = request_id


logger.remove()

logger = logger.patch(inject_request_id)
if conf.logging.console.enable:
    logger.add(sink=sys.stdout, level=conf.logging.console.level, format=log_format)
if conf.logging.file.enable:
    path = Path(conf.logging.file.path)
    path.mkdir(parents=True, exist_ok=True)
    logger.add(
        sink=path / "app.log",
        level=conf.logging.file.level,
        format=log_format,
        rotation=conf.logging.file.rotation,
        retention=conf.logging.file.retention,
        encoding="utf-8"
    )

