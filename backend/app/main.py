"""
Eye in the Sky API
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.routers import (
    auth,
    constellations,
    celestial,
    quiz,
    skyinfo,
    watchlist,
    user_settings,
    starmap,
    lessons,
    events,
    satellites,
    sky_routes,
    payments,
    jwst,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Registered Routes:")
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = ",".join(route.methods)
            logger.info(f"{methods:10s} | {route.path}")
    yield


app = FastAPI(
    title="Eye in the Sky API",
    description="Celestial object identification, AR astronomy, and subscription management.",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(constellations.router)
app.include_router(celestial.router)
app.include_router(quiz.router)
app.include_router(skyinfo.router)
app.include_router(watchlist.router)
app.include_router(user_settings.router)
app.include_router(starmap.router)
app.include_router(lessons.router)
app.include_router(events.router)
app.include_router(satellites.router)
app.include_router(sky_routes.router)
app.include_router(payments.router)
app.include_router(jwst.router)


@app.get("/")
def root():
    return {"message": "Eye in the Sky API is running!", "version": "1.1.0"}
