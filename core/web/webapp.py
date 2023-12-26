from core.config.config import yeti_config
from core.logger import logger
from core.web.apiv2 import (auth, entities, graph, indicators, observables,
                            system, tag, tasks, templates, users)
from fastapi import APIRouter, Depends, FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.types import Message

SECRET_KEY = yeti_config.get('auth', "secret_key")

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

api_router.include_router(
    observables.router, prefix="/observables", tags=["observables"],
    dependencies=[Depends(auth.get_current_active_user)]
)
api_router.include_router(
    entities.router, prefix="/entities", tags=["entities"],
    dependencies=[Depends(auth.get_current_active_user)]
)
api_router.include_router(
    indicators.router, prefix="/indicators", tags=["indicators"],
    dependencies=[Depends(auth.get_current_active_user)]
)
api_router.include_router(
    tag.router, prefix="/tags", tags=["tags"],
    dependencies=[Depends(auth.get_current_active_user)]
)
api_router.include_router(
    tasks.router, prefix="/tasks", tags=["tasks"],
    dependencies=[Depends(auth.get_current_active_user)]
)
api_router.include_router(
    graph.router, prefix="/graph", tags=["graph"],
    dependencies=[Depends(auth.get_current_active_user)]
)
api_router.include_router(
    templates.router, prefix="/templates", tags=["templates"],
    dependencies=[Depends(auth.get_current_active_user)]
)
api_router.include_router(
    users.router, prefix="/users", tags=["users"],
    dependencies=[Depends(auth.get_current_active_user)]
)
# Dependencies are set in system endpoints
api_router.include_router(
    system.router, prefix="/system", tags=["system"],
)

app.include_router(api_router, prefix="/api/v2")

async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {'type': 'http.request', 'body': body}
    request._receive = receive

@app.middleware("http")
async def log_requests(request: Request, call_next):

    req_body = await request.body()
    await set_body(request, req_body)
    response = await call_next(request)
    if getattr(request.state, 'username', None):
        extra = {
            "username": request.state.username,
            "path": request.url.path,
            "method": request.method,
        }
        if request.method == "POST":
            try:
                extra["body"] = req_body
            except:
                extra["body"] = None
        if response.status_code == 200:
            logger.info("Authorized request", extra=extra)
        elif response.status_code == 401:
            logger.info("Unauthorized request", extra=extra)
    return response
