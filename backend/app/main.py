from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
import logging

# === Routers ===
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
)

app = FastAPI(
    title="Eye in the Sky API",
    description="Celestial object identification and AR astronomy API.",
    version="1.0.0"
)

# === CORS Configuration ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can narrow this down later for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Include Routers ===
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

# === Root Endpoint ===
@app.get("/")
def root():
    return {"message": "🌌 Eye in the Sky API is running!"}

# === Startup Route Logger ===
@app.on_event("startup")
async def list_routes():
    logging.basicConfig(level=logging.INFO)
    logging.info("🚀 Registered Routes:")
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = ",".join(route.methods)
            logging.info(f"{methods:10s} | {route.path}")