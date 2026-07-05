from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, health


def create_app() -> FastAPI:
    app = FastAPI(title="AutoPilotAI API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)

    return app


app = create_app()
