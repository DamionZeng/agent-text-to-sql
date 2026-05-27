import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers.query_router import query_router
from app.api.routers.metadata_router import metadata_router
from app.api.routers.health_router import health_router
from app.api.routers.viz_router import router as viz_router
from app.api.routers.dataset_router import router as dataset_router
from app.api.routers.data_screen_router import router as data_screen_router
from app.core.context import request_id_ctx_var
from app.core.lifespan import lifespan
from app.core.log import logger

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router)
app.include_router(metadata_router)
app.include_router(health_router)
app.include_router(viz_router)
app.include_router(dataset_router)
app.include_router(data_screen_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"}
    )

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    request_id_ctx_var.set(uuid.uuid4())
    response = await call_next(request)
    return response
