from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import chores, dashboard, users

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Chores Hub API",
    description="Backend for the household chores tracking display.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(chores.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok"}
