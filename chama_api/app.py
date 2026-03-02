"""Application factory for chama-api."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chama_api.routers import chamas, members, contributions, loans, health


def create_app(*, cors_origins: list[str] | None = None) -> FastAPI:
    app = FastAPI(
        title="chama-api",
        description=(
            "REST API for chama (ROSCA) management.\n\n"
            "Built on [chama-protocol](https://github.com/gabrielmahia/chama-protocol) — "
            "the domain library for Kenya's rotating credit associations."
        ),
        version="1.0.0",
        contact={"name": "Gabriel Mahia", "email": "contact@aikungfu.dev"},
        license_info={"name": "CC BY-NC-ND 4.0", "url": "https://creativecommons.org/licenses/by-nc-nd/4.0/"},
        openapi_tags=[
            {"name": "health",        "description": "Service health"},
            {"name": "chamas",        "description": "Chama lifecycle"},
            {"name": "members",       "description": "Member management"},
            {"name": "contributions", "description": "Contribution recording and history"},
            {"name": "loans",         "description": "Loan issuance and tracking"},
        ],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(chamas.router,        prefix="/chamas",        tags=["chamas"])
    app.include_router(members.router,       prefix="/chamas",        tags=["members"])
    app.include_router(contributions.router, prefix="/chamas",        tags=["contributions"])
    app.include_router(loans.router,         prefix="/chamas",        tags=["loans"])
    return app
