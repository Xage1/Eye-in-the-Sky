from fastapi import FastAPI
from app.routers import constellations, events, news, user

app = FastAPI(title="Eye-in-the-Sky")

# Routers
app.include_router(constellations.router)
app.include_router(events.router)
app.include_router(news.router)
app.include_router(user.router)


@app.get("/")
async def root():
    return {"message": "Welcome to Eye in the Sky API"}