# 🌌 Eye in the Sky

> A comprehensive Android astronomy app combining real-time AR star mapping, satellite tracking, celestial event alerts, and astronomy education — built for curious minds everywhere.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [External APIs & Data Sources](#external-apis--data-sources)
- [Database Schema](#database-schema)
- [AR Coordinate System](#ar-coordinate-system)
- [Sound Design](#sound-design)
- [Roadmap](#roadmap)
- [Known Issues](#known-issues)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Eye in the Sky** is an Android astronomy companion app that merges real-time augmented reality with structured learning and live celestial data. Point your phone at the sky to identify stars, planets, and constellations. Track satellites passing overhead. Get notified about upcoming meteor showers, eclipses, and ISS flyovers. Learn astronomy from scratch through interactive lessons and quizzes — all in one app.

Built with **Kotlin + Jetpack Compose** on Android and a **Python (FastAPI) + PostgreSQL + Redis** backend, containerised with **Docker**.

---

## Features

### 1. Sky Guide / Star Map (AR)
- Real-time AR overlay using device GPS and gyroscope
- Identifies stars, planets, and constellations as you point your camera at the sky
- Tap any celestial object to learn about it — mythology, distance, magnitude, and more
- Night mode for dark-sky viewing (red-tinted UI preserves night vision)
- Constellation line drawing with mythology cards
- Star watchlist — save your favourite objects

### 2. Astronomy 101 (Learning)
- Beginner-friendly structured lessons: stars, galaxies, planets, black holes, nebulae, and more
- Interactive quizzes with instant scoring and answer explanations
- Flashcard mode for quick revision
- Difficulty levels: beginner, intermediate, advanced
- Progress tracking per user
- Illustrated mini-lessons with rich constellation and object data

### 3. Night Sky Watch (Events)
- Real-time data on upcoming celestial events: meteor showers, lunar/solar eclipses, planetary alignments, ISS flyovers
- Local weather forecasts integrated with visibility scores
- Push notifications for events visible from your location
- Historical event archive — browse past celestial events
- Famous astronomer quotes tied to relevant events

### 4. Satellite Locator
- Live positions of major satellites using NORAD TLE data
- Visual map showing satellite ground tracks
- Satellite info cards — what each satellite does, who operates it, orbital details
- ISS real-time position and next flyover prediction for your location
- TLE data refreshed every 6 hours via background worker

---

## Tech Stack

| Layer | Technology |
|---|---|
| Android UI | Kotlin, Jetpack Compose, Material 3 |
| AR Overlay | CameraX, Android SensorManager (rotation vector fusion) |
| Networking | Retrofit 2, OkHttp, Moshi |
| Audio | SoundPool (SFX), ExoPlayer (ambient audio) |
| Animations | Lottie for Compose |
| Backend API | Python 3.11, FastAPI, Uvicorn |
| ORM | SQLAlchemy (async), Alembic (migrations) |
| Database | PostgreSQL 15 |
| Cache / Pub-Sub | Redis 7 |
| Background Jobs | Celery + Redis broker |
| Containerisation | Docker, Docker Compose |
| Location Services | Google Play Services (FusedLocationProvider) |
| External Data | CelesTrak, NASA APIs, Open Notify, OpenWeather |

---

## Architecture


![Eye in the Sky Architecture](./assets/eye_in_the_sky_architecture.svg)

```
┌─────────────────────────────────────────────────────────────┐
│               Android App (Kotlin / Jetpack Compose)        │
│                                                             │
│  AR Star Map  │  Astronomy 101  │  Sky Watch  │  Satellites │
│                                                             │
│  CameraX + SensorManager → AR overlay renderer              │
│  Retrofit / OkHttp → FastAPI backend (HTTPS)                │
└─────────────────────────────────────────────────────────────┘
                            │ HTTPS / WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Python FastAPI Gateway                         │
│                                                             │
│  Auth  │  Quiz/Lesson  │  Sky Engine  │  Events  │  TLE     │
│                                                             │
│  Redis cache  <->  Celery workers (TLE refresh, alerts)     │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
             ▼                           ▼
     ┌───────────────┐         ┌──────────────────────┐
     │  PostgreSQL   │         │   External APIs      │
     │               │         │                      │
     │  Users        │         │  CelesTrak (TLE)     │
     │  Quiz/Lessons │         │  NASA APOD / Events  │
     │  Events       │         │  Open Notify (ISS)   │
     │  Watchlist    │         │  OpenWeather         │
     │  Locations    │         │  Stellarium catalog  │
     └───────────────┘         └──────────────────────┘
```

---

## Project Structure

```
eye-in-the-sky/
│
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 689451688bf6_initial_full_schema.py
│   │   ├── env.py
│   │   └── script.py.mako
│   └── app/
│       ├── controllers/
│       │   └── skyController.py          # AR coordinate engine (in progress)
│       ├── data/
│       │   └── constellations.json       # 88 constellations with mythology
│       ├── models/
│       │   ├── user.py
│       │   ├── user_settings.py
│       │   ├── location.py
│       │   ├── quiz.py
│       │   ├── quiz_answer.py
│       │   ├── quiz_submission.py
│       │   ├── lesson.py
│       │   └── star_watchlist.py
│       ├── routers/                      # FastAPI route handlers
│       ├── services/
│       │   ├── tle_service.py            # Satellite TLE fetch + parse
│       │   ├── weather_service.py        # OpenWeather integration
│       │   └── event_service.py          # Celestial event scheduling
│       └── database.py
│
├── frontend/
│   └── app/src/main/
│       ├── java/com/eye/sky/
│       │   ├── MainActivity.kt
│       │   ├── audio/
│       │   │   └── SoundManager.kt
│       │   ├── ui/
│       │   │   ├── AppRoot.kt
│       │   │   └── screens/
│       │   │       ├── StarMapScreen.kt
│       │   │       ├── LessonsScreen.kt
│       │   │       ├── QuizScreen.kt
│       │   │       ├── SatelliteScreen.kt
│       │   │       └── EventsScreen.kt
│       │   ├── ar/
│       │   │   └── SkyOverlayRenderer.kt
│       │   └── viewmodels/
│       │       └── QuizViewModel.kt
│       ├── res/raw/
│       │   ├── galaxy_tap.wav
│       │   ├── meteor_swipe.wav
│       │   ├── nebula_pad.m4a
│       │   ├── blackhole_loader.wav
│       │   ├── eclipse_toggle.wav
│       │   └── planet_alignment.wav
│       └── AndroidManifest.xml
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Getting Started

### Prerequisites

- **Android Studio** Hedgehog (2023.1.1) or newer
- **Android device or emulator** running API 24+ (Android 7.0+)
- **Python 3.11+**
- **Docker & Docker Compose**
- **PostgreSQL 15** (or use the Docker Compose setup)
- **Redis 7** (or use the Docker Compose setup)

### Backend Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/eye-in-the-sky.git
cd eye-in-the-sky/backend

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your API keys and DB credentials

# 5. Run database migrations
alembic upgrade head

# 6. Start the API server
uvicorn app.main:app --reload --port 8000
```

**Or spin up the full stack with Docker:**

```bash
docker-compose up --build
```

API: `http://localhost:8000`
Swagger docs: `http://localhost:8000/docs`

### Frontend Setup

1. Open **Android Studio** → **Open** → select the `frontend/` directory
2. Wait for Gradle sync to complete
3. Update `BASE_URL` in `network/ApiClient.kt` to point to your backend
4. Run on a **physical device** — AR features require real sensors
5. Grant Camera and Location permissions when prompted

> AR star mapping requires a physical device with a working compass, gyroscope, and accelerometer. Emulators will not produce accurate results.

### Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/eyeinthesky
DATABASE_URL_SYNC=postgresql://user:password@localhost:5432/eyeinthesky

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Auth
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# External APIs
OPENWEATHER_API_KEY=your_openweather_key
NASA_API_KEY=your_nasa_api_key        # Free key at https://api.nasa.gov
CELESTRAK_BASE_URL=https://celestrak.org/SOCRATES/
OPEN_NOTIFY_URL=http://api.open-notify.org

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create a new user account |
| `POST` | `/auth/login` | Authenticate and receive a JWT token |
| `GET` | `/sky/stars` | Stars visible from a given lat/lon |
| `GET` | `/sky/constellations` | All 88 constellations with mythology |
| `GET` | `/sky/planets` | Current planet positions |
| `GET` | `/satellites/` | List of tracked satellites |
| `GET` | `/satellites/{norad_id}/position` | Live position of a specific satellite |
| `GET` | `/satellites/iss/flyovers` | ISS flyover times for a given location |
| `GET` | `/events/upcoming` | Upcoming celestial events |
| `GET` | `/events/history` | Historical celestial event archive |
| `GET` | `/weather/visibility` | Sky visibility score for a location |
| `GET` | `/lessons/` | List all astronomy lessons |
| `GET` | `/lessons/{id}` | Single lesson with full content |
| `GET` | `/quiz/questions` | Quiz questions (filterable by difficulty) |
| `POST` | `/quiz/submit` | Submit quiz answers and receive a score |
| `GET` | `/watchlist/` | User's saved star watchlist |
| `POST` | `/watchlist/` | Add a celestial object to the watchlist |
| `DELETE` | `/watchlist/{id}` | Remove an object from the watchlist |

---

## External APIs & Data Sources

| Service | Purpose | Cost |
|---|---|---|
| [CelesTrak](https://celestrak.org) | TLE orbital data for 20,000+ satellites | Free |
| [Space-Track (NORAD)](https://www.space-track.org) | Authoritative TLE source | Free (registration required) |
| [NASA APIs](https://api.nasa.gov) | APOD, solar events, near-earth objects | Free |
| [Open Notify](http://open-notify.org) | ISS real-time position and flyover predictions | Free |
| [OpenWeather](https://openweathermap.org/api) | Cloud cover and atmospheric clarity scores | Free tier available |
| [Stellarium Web Engine](https://github.com/Stellarium/stellarium-web-engine) | Star catalog reference data | Open source |

---

## Database Schema

All tables managed via Alembic migrations in `backend/alembic/versions/`.

| Table | Purpose |
|---|---|
| `users` | User accounts and hashed credentials |
| `user_settings` | Per-user preferences (night mode, units, notifications) |
| `lessons` | Astronomy 101 lesson content with difficulty levels |
| `quiz_questions` | Quiz question bank |
| `quiz_answers` | Answer options per question |
| `quiz_submissions` | User quiz attempts and scores |
| `location_entries` | GPS history for personalised sky data |
| `star_watchlist` | User-saved stars, planets, and deep-sky objects |

Run `alembic upgrade head` to apply all migrations.
Run `alembic downgrade -1` to roll back one step.

---

## AR Coordinate System

The AR star map pipeline runs every frame at ~30fps:

```
GPS + IMU sensors + UTC time
        │
        ▼
Device orientation matrix
(SensorManager TYPE_ROTATION_VECTOR — fuses accel + gyro + compass)
        │
        ▼
Local Sidereal Time (LST)
LST = Greenwich Mean Sidereal Time + longitude offset
        │
        ▼
RA / Dec  →  Altitude / Azimuth
Hour Angle (HA) = LST − Right Ascension
sin(Alt) = sin(Dec)sin(Lat) + cos(Dec)cos(Lat)cos(HA)
        │
        ▼
Alt/Az → camera-relative 3D vector (apply device rotation matrix)
        │
        ▼
Perspective projection → screen pixel (x, y)
(FOV + screen dimensions)
        │
        ▼
Canvas / OpenGL AR overlay render
(magnitude filter: hide stars dimmer than mag 5.0 in dense sky regions)
```

Stars behind the device (negative z after rotation) are culled before projection. The coordinate math lives in `backend/app/controllers/skyController.py` and is mirrored on the client in `ar/SkyOverlayRenderer.kt`.

---

## Sound Design

UI interactions are mapped to space-themed audio cues:

| Sound File | UI Trigger |
|---|---|
| `galaxy_tap.wav` | Button taps and small UI interactions |
| `meteor_swipe.wav` | Quiz question next / previous swipe |
| `blackhole_loader.wav` | Loading heavy tasks (shows BlackHoleLoader animation) |
| `eclipse_toggle.wav` | Password visibility toggle |
| `planet_alignment.wav` | Quiz submit success / achievement unlocked |
| `nebula_pad.m4a` | Tab switches and lesson open (short ambient loop) |

Audio is managed by `SoundManager` — `SoundPool` for low-latency SFX, `ExoPlayer` for streamed ambient tracks.

---

## Roadmap

### v1.0 — MVP (Current Focus)
- [x] Project scaffolding — backend and frontend
- [x] User auth (register / login / JWT)
- [x] Database schema and Alembic migrations
- [x] Constellation data (all 88 constellations with mythology)
- [x] Quiz system (ViewModel + API layer)
- [x] Lesson content model
- [x] CameraX AR scaffold
- [x] Sound system (SoundManager + SFX mapping)
- [ ] Fix `build.gradle.kts` Groovy/KTS syntax issue (Lottie + ExoPlayer)
- [ ] `skyController.py` — AR coordinate engine implementation
- [ ] AR canvas overlay renderer in Kotlin (star projection)
- [ ] Star catalog integration (Hipparcos / Yale BSC)

### v1.1 — Satellite Tracking
- [ ] TLE fetch and parse service (CelesTrak via sgp4)
- [ ] Satellite position calculations
- [ ] ISS flyover predictions (Open Notify)
- [ ] Satellite screen UI in Kotlin
- [ ] Celery worker for TLE refresh every 6 hours

### v1.2 — Events & Weather
- [ ] Celestial events service (meteor showers, eclipses, planetary alignments)
- [ ] OpenWeather visibility score integration
- [ ] Push notifications for upcoming events
- [ ] Historical events archive UI

### v1.3 — Polish & Growth
- [ ] Full night mode (red-tinted UI for dark-sky preservation)
- [ ] Astronomer quotes section
- [ ] Flashcard mode for lessons
- [ ] Offline mode for lessons and star catalog
- [ ] Localization — Swahili (sw) support
- [ ] Google Play Store release

---

## Known Issues

| Issue | Status |
|---|---|
| `build.gradle.kts` mixes Groovy string syntax with Kotlin DSL — causes compile errors for Lottie and ExoPlayer deps | Needs fix |
| `skyController.py` is an empty placeholder | In progress |
| `AndroidManifest.xml` missing `INTERNET` permission declaration | Needs fix |
| `SoundManager` references nested resource path `R.raw.ui.galaxy_tap` — Android does not support subdirectory raw resources | Needs fix |

---

## Contributing

Contributions, bug reports, and feature suggestions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit with a clear message: `git commit -m "feat: describe your change"`
4. Push to your branch: `git push origin feature/your-feature-name`
5. Open a Pull Request against `main`

Please follow the existing code style and include unit tests where relevant.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

> *"The cosmos is within us. We are made of star-stuff. We are a way for the universe to know itself."*
> — Carl Sagan
