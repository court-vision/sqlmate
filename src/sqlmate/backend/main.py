import json
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
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
    uvicorn.run("sqlmate.backend.main:app", host="::", port=PORT)
