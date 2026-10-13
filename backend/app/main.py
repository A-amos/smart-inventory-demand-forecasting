from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.auth import router
from app.api.catalog import router as catalog_router
from app.api.sales import router as sales_router
from app.api.decisions import router as decisions_router
from app.core.config import Settings
from app.database import SessionLocal


def create_app(settings: Settings | None = None):
    app = FastAPI(title="Smart Inventory API", version="0.1.0")
    app.state.settings = settings or Settings()
    app.state.session_factory = SessionLocal
    app.add_middleware(CORSMiddleware, allow_origins=app.state.settings.cors_origins,
                       allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                       allow_headers=["Authorization", "Content-Type"])
    app.include_router(router)
    app.include_router(catalog_router)
    app.include_router(sales_router)
    app.include_router(decisions_router)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        return JSONResponse(status_code=503, content={"detail": "Database temporarily unavailable"})

    @app.get("/api/v1/health/live", tags=["Health"])
    def live():
        return {"status": "ok"}

    @app.get("/api/v1/health/ready", tags=["Health"])
    def ready():
        with app.state.session_factory() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ready"}

    return app


app = create_app()
