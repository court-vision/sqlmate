import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmate.backend.utils.constants import PORT
from sqlmate.backend.routers import auth, user_data, query

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://sqlmate-ruddy.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return "Welcome to SQLMate API!"

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "SQLMate API is running"}

app.include_router(router=auth.router, prefix="/auth")
app.include_router(router=user_data.router, prefix="/users")
app.include_router(router=query.router, prefix="/query")

if __name__ == "__main__":
    # We're installed as a package
    uvicorn.run("sqlmate.backend.main:app", host="0.0.0.0", port=PORT)