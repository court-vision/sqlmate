import json
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlmate.backend.utils.constants import PORT, SQLMATE_SCHEMA_DIR
from sqlmate.backend.routers import auth, user_data, query
from sqlmate.backend.startup import run_startup


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    run_startup()
    yield
    # Shutdown (nothing needed)


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://sqlmate-ruddy.vercel.app",
        "https://sqlmate.courtvision.dev",
        "https://courtvision.dev",
        "https://www.courtvision.dev",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_csp_header(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "frame-ancestors 'self' https://courtvision.dev https://www.courtvision.dev https://sqlmate.courtvision.dev"
    )
    return response


@app.get("/")
def home():
    return "Welcome to SQLMate API!"


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "SQLMate API is running"}


@app.get("/schema")
def get_schema():
    schema_path = os.path.join(SQLMATE_SCHEMA_DIR, "db_schema.json")
    if not os.path.exists(schema_path):
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Schema not found. Startup may not have run yet."},
        )
    with open(schema_path, "r") as f:
        schema = json.load(f)
    return schema


app.include_router(router=auth.router, prefix="/auth")
app.include_router(router=user_data.router, prefix="/users")
app.include_router(router=query.router, prefix="/query")

if __name__ == "__main__":
    # We're installed as a package
    uvicorn.run("sqlmate.backend.main:app", host="0.0.0.0", port=PORT)
