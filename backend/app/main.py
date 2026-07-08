from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth, health, matches, resumes


def create_app() -> FastAPI:
    app = FastAPI(title="AutoPilotAI API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(resumes.router)
    app.include_router(matches.router)

    return app


app = create_app()
