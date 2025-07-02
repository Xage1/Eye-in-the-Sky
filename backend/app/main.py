from fastapi import FastAPI
from app.routers import constellations, celestial, quiz
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(constellations.router)
app.include_router(celestial.router)
app.include_router(quiz.router)