from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import create_table
import database.models as models
from routes.users import router as users_router
from routes.ideas import router as ideas_router
from routes.conversations import router as conversations_router

create_table()

app = FastAPI(title="Business Idea Validator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(ideas_router)
app.include_router(conversations_router)

@app.get("/")
def health_check():
    return {"message": "Business validator api is running smoothly."}