from fastapi import FastAPI
from app.routers import constellations, celestial, quiz
from app.routers import location
from app.routers import auth
from app.routers import skyinfo
from app.routers import quiz, watchlist, user_settings, starmap, lessons, events, satellites, sky_routes
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI()

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
app.include_router(satellites.router)
app.include_router(sky_routes.router)



@app.on_event("startup")
async def list_routes():
    logging.info("🚀 Registered Routes:")
    for route in app.routes:
        if hasattr(route, 'methods'):
            methods = ",".join(route.methods)
            logging.info(f"{methods:10s} | {route.path}")