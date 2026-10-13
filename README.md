# Eye in the Sky

> A comprehensive Android astronomy app combining real-time AR star mapping, satellite tracking, celestial event alerts, real James Webb Space Telescope imagery, and astronomy education -- built for curious minds everywhere.

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

**Eye in the Sky** is an Android astronomy companion app that merges real-time augmented reality with structured learning and live celestial data. Point your phone at the sky to identify stars, planets, and constellations. Track satellites passing overhead. Get notified about upcoming meteor showers and eclipses. Search and download real James Webb Space Telescope imagery for any target. Learn astronomy from scratch through interactive lessons and quizzes -- all in one app.

Built with **Kotlin + Jetpack Compose** on Android and a **Python (FastAPI) + PostgreSQL + Redis + Celery** backend, containerised with **Docker**. A Free / Pro / Premium subscription model (Stripe, M-Pesa, Paystack) gates the heavier features.

---

## Features

### 1. Sky Guide / Star Map (AR)
- Real-time AR overlay using device GPS and gyroscope
- Identifies stars, planets, and constellations as you point your camera at the sky
- Tap any celestial object to learn about it -- mythology, distance, magnitude, and more
- Constellation line drawing with mythology cards
- Star watchlist -- save your favourite objects

### 2. Astronomy 101 (Learning)
- Beginner-friendly structured lessons: stars, galaxies, planets, black holes, nebulae, and more, filterable by category
- Interactive quizzes with instant scoring and submission history
- Illustrated mini-lessons with rich constellation and object data

### 3. Night Sky Watch (Events & Alerts)
- `solar_events` table seeded with real recurring meteor showers (radiant, ZHR, parent body) and verified 2026-2027 solar/lunar eclipse dates (NASA / EclipseWise)
- A daily Celery Beat task scans for events in the next 48 hours and creates an in-app notification for every opted-in user whose saved location falls within the event's visible latitude range
- In-app notification feed: list, unread count, mark-as-read
- Live `/events/night-sky` endpoint combines real-time astronomy-event data with a weather visibility forecast for a given lat/lon

### 4. Stargazing Visibility Score
- Every saved location gets a cached 0-100 visibility score (`100 - cloud_cover%`, with a humidity penalty for hazy skies), refreshed every 3 hours by a Celery task
- Reuses the same OpenWeather-backed scoring engine that powers the live `GET /skyinfo/visibility` endpoint
- Locations are deduplicated by coordinate before hitting the weather API, so users clustered in the same area share one API call

### 5. Satellite Locator
- Live TLE orbital data for 20,000+ satellites, refreshed from CelesTrak every 6 hours via a Celery Beat task and cached in Redis
- Visible-satellite lookup for a given location

### 6. JWST Deep Space Explorer (Premium)
- Free-text search against the MAST archive (`astroquery`) for public James Webb Space Telescope mosaic imagery of any target -- nebulae, galaxies, star-forming regions
- Background download and processing pipeline: downloads the FITS mosaic, applies a ZScale + Asinh stretch (astropy), and renders a publication-quality PNG preview with detector-gap seams rendered black instead of the default white
- Full request lifecycle (`pending -> downloading -> processing -> completed/failed`) pollable by the client, with a dedup cache so a previously-downloaded product is never re-fetched
- Gated behind a Pro or Premium subscription

### 7. Subscriptions & Payments
- Free / Pro / Premium plan tiers
- Stripe (card payments), M-Pesa STK Push (Kenya), and Paystack integrations, with webhook and callback handling
- Transaction history and self-service plan management

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
| ORM | SQLAlchemy (async for the API, sync for Celery tasks), Alembic (migrations) |
| Database | PostgreSQL 15 |
| Cache / Broker | Redis 7 |
| Background Jobs | Celery + Celery Beat (Redis broker) |
| Astronomy / Imaging | astropy, astroquery (MAST archive client), numpy, matplotlib |
| Payments | Stripe, M-Pesa Daraja API, Paystack |
| Containerisation | Docker, Docker Compose |
| Location Services | Google Play Services (FusedLocationProvider) on-device; OpenStreetMap Nominatim for reverse geocoding on the backend |
| External Data | CelesTrak, MAST/astroquery, AstronomyAPI, OpenWeather, Open Notify, N2YO |

---

## Architecture

```
+---------------------------------------------------------------+
|               Android App (Kotlin / Jetpack Compose)          |
|                                                                 |
|  AR Star Map  |  Astronomy 101  |  Sky Watch  |  Satellites   |
|                                                                 |
|  CameraX + SensorManager -> AR overlay renderer                |
|  Retrofit / OkHttp -> FastAPI backend (HTTPS)                  |
+---------------------------------------------------------------+
                            | HTTPS
                            v
+---------------------------------------------------------------+
|              Python FastAPI Gateway                           |
|                                                                 |
|  Auth | Quiz/Lesson | SkyInfo | Events | Notifications | JWST  |
|  Location | Satellites | Payments                             |
|                                                                 |
|  Redis cache/broker  <->  Celery workers + Beat scheduler      |
+--------------+-----------------------------+-------------------+
               |                             |
               v                             v
      +-----------------+         +--------------------------+
      |   PostgreSQL    |         |   External APIs          |
      |                 |         |                           |
      |  Users          |         |  CelesTrak (TLE)          |
      |  Subscriptions   |         |  MAST / astroquery (JWST) |
      |  Quiz/Lessons    |         |  AstronomyAPI             |
      |  solar_events    |         |  Open Notify (ISS)        |
      |  notifications   |         |  OpenWeather              |
      |  location_entries|         |  N2YO                     |
      |  jwst_requests   |         |  OpenStreetMap Nominatim  |
      |  star_watchlist  |         |  Stripe / M-Pesa / Paystack|
      +-----------------+         +--------------------------+
```

Celery Beat currently drives three recurring jobs: TLE refresh (every 6h), celestial-event alert scan (daily at midnight UTC), and visibility-score refresh (every 3h). JWST image processing runs on its own queue (`jwst_processing`) since downloads can be hundreds of megabytes and take minutes.

---

## Project Structure

```
eye-in-the-sky/
|-- backend/
|   |-- alembic/
|   |   |-- versions/
|   |   |   |-- 2b92cbb2c6bd_initial_full_schema.py
|   |   |   |-- 143a9e151eaf_add_jwst_requests_table.py
|   |   |   |-- a1f3c9d2e766_add_notifications_table.py
|   |   |   |-- f2a7b9c1d834_add_visibility_score_to_locations.py
|   |   |-- env.py
|   |   |-- script.py.mako
|   |-- scripts/
|   |   |-- seed_solar_events.py        # seeds solar_events: meteor showers + eclipses
|   |-- app/
|       |-- controllers/
|       |   |-- skyController.py        # moon phase, rise/set, visibility score, AR scene, ISS
|       |-- services/
|       |   |-- jwst_service.py         # MAST search/download + FITS -> preview rendering
|       |-- tasks/                      # Celery Beat jobs
|       |   |-- tle_tasks.py
|       |   |-- event_tasks.py
|       |   |-- weather_tasks.py
|       |   |-- jwst_tasks.py
|       |-- models/
|       |   |-- user.py, user_settings.py, location.py, subscription.py
|       |   |-- lesson.py, quiz.py, quiz_answer.py, quiz_submission.py
|       |   |-- star.py, star_watchlist.py, quote.py
|       |   |-- solar_event.py, notification.py, jwst_request.py
|       |-- routers/                    # FastAPI route handlers (see API Reference)
|       |-- schemas/                    # Pydantic request/response models
|       |-- utils/
|       |   |-- deps.py                 # auth + DB session + Pro/Premium/admin gates
|       |   |-- sync_db.py              # sync SQLAlchemy session for Celery tasks
|       |   |-- security.py, auth.py
|       |   |-- astronomy.py, geo.py, tle.py, stars.py, sky_tools.py, satellite_tools.py
|       |-- database.py, main.py, worker.py
|
|-- frontend/
|   |-- app/src/main/
|       |-- java/com/eye/sky/
|       |   |-- MainActivity.kt
|       |   |-- audio/
|       |   |   |-- SoundManager.kt
|       |   |-- ui/
|       |   |   |-- AppRoot.kt
|       |   |   |-- screens/
|       |   |       |-- StarMapScreen.kt
|       |   |       |-- LessonsScreen.kt
|       |   |       |-- QuizScreen.kt
|       |   |       |-- SatelliteScreen.kt
|       |   |       |-- EventsScreen.kt
|       |   |-- ar/
|       |   |   |-- SkyOverlayRenderer.kt
|       |   |-- viewmodels/
|       |       |-- QuizViewModel.kt
|       |-- res/raw/
|       |   |-- galaxy_tap.wav, meteor_swipe.wav, nebula_pad.m4a
|       |   |-- blackhole_loader.wav, eclipse_toggle.wav, planet_alignment.wav
|       |-- AndroidManifest.xml
|
|-- docker-compose.yml
|-- .env.example
|-- README.md
```

> The frontend tree above reflects the last known layout; this backend-focused sprint did not audit the Android code, so some items here (AR renderer, sound hookups) should be verified against the current state of `frontend/` directly.

---

## Getting Started

### Prerequisites

- **Android Studio** Hedgehog (2023.1.1) or newer
- **Android device or emulator** running API 24+ (Android 7.0+)
- **Docker & Docker Compose** (recommended -- runs Postgres, Redis, the API, Celery worker, and Celery Beat together)
- **Python 3.11+** (only needed for running the backend outside Docker)

### Backend Setup (Docker -- recommended)

```bash
git clone https://github.com/Xage1/Eye-in-the-Sky.git
cd Eye-in-the-Sky

cp backend/.env.example backend/.env
# Edit backend/.env with your DB credentials and API keys (see below)

docker compose up --build
```

API: `http://localhost:8000`
Swagger docs: `http://localhost:8000/docs`

Migrations run automatically on container start. To run them manually, or to seed the celestial-events data:

```bash
docker exec eyesky_api alembic upgrade head
docker exec eyesky_api python scripts/seed_solar_events.py
```

### Backend Setup (bare metal)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. Open **Android Studio** -> **Open** -> select the `frontend/` directory
2. Wait for Gradle sync to complete
3. Update the backend base URL to point to your running API
4. Run on a **physical device** -- AR features require real sensors
5. Grant Camera and Location permissions when prompted

> AR star mapping requires a physical device with a working compass, gyroscope, and accelerometer. Emulators will not produce accurate results.

### Environment Variables

The real variables read by the backend (see `backend/app/utils/`, `app/worker.py`, `docker-compose.yml`):

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=eye_db
DATABASE_URL=postgresql+asyncpg://postgres:your_password@postgres:5432/eye_db
DATABASE_URL_SYNC=postgresql://postgres:your_password@postgres:5432/eye_db

# Redis (Celery broker + result backend)
REDIS_URL=redis://redis:6379/0

# JWT Auth
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Payments
MPESA_CONSUMER_KEY=
MPESA_CONSUMER_SECRET=
MPESA_SHORTCODE=
MPESA_PASSKEY=
MPESA_CALLBACK_URL=
MPESA_ENV=sandbox
PAYSTACK_SECRET_KEY=
PAYSTACK_PUBLIC_KEY=
PAYSTACK_CALLBACK_URL=

# External data APIs
ASTRONOMY_API_KEY=         # astronomyapi.com
WEATHER_API_KEY=           # OpenWeather
N2YO_API_KEY=
NASA_API_KEY=
OPEN_NOTIFY_ISS_URL=http://api.open-notify.org/iss-now.json
CELESTRAK_URL=https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle

ADMIN_EMAILS=
```

> `WEATHER_API_KEY` is currently consumed by two different implementations (`app/controllers/skyController.py` + `app/utils/astronomy.py` expect an OpenWeather key; `app/utils/weather.py`, used by `/events/night-sky`, expects a weatherapi.com key). See [Known Issues](#known-issues).

---

## API Reference

Full interactive reference: `http://localhost:8000/docs` (Swagger) once the API is running. The table below is the verified route list as of this write-up.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/signup` | -- | Create a new user account |
| `POST` | `/auth/login` | -- | Authenticate and receive a JWT |
| `GET` | `/auth/me` | user | Current user profile |
| `PATCH` | `/auth/me` | user | Update current user profile |
| `POST` | `/auth/change-password` | user | Change password |
| `POST` | `/auth/deactivate` | user | Deactivate own account |
| `GET` | `/auth/admin/users` | admin | List all users |
| `PATCH` | `/auth/admin/users/{user_id}/role` | admin | Change a user's role |
| `GET` | `/skyinfo/moon-phase` | user | Current moon phase (pure calculation, no API key) |
| `GET` | `/skyinfo/visibility` | user | Stargazing visibility score for a lat/lon (OpenWeather) |
| `GET` | `/skyinfo/rise-set` | user | Star/planet rise & set times (AstronomyAPI) |
| `GET` | `/skyinfo/scene` | user | Full AR sky scene (master frame endpoint) |
| `GET` | `/skyinfo/planets` | user | Planet positions for an observer location |
| `GET` | `/skyinfo/iss` | user | Live ISS position + visibility flag |
| `GET` | `/skyinfo/events` | user | Upcoming celestial events (live AstronomyAPI) |
| `GET` | `/skyinfo/star/{name}` | user | Tap-to-learn star detail |
| `GET` | `/events/` | user | Celestial events list |
| `GET` | `/events/night-sky` | user | Combined astronomy events + weather visibility for a lat/lon |
| `GET` | `/notifications` | user | List current user's in-app notifications |
| `GET` | `/notifications/unread-count` | user | Unread notification badge count |
| `PATCH` | `/notifications/read-all` | user | Mark all notifications read |
| `PATCH` | `/notifications/{id}/read` | user | Mark one notification read |
| `POST` | `/location/store` | user | Save a reverse-geocoded location |
| `GET` | `/location/history` | user | List saved locations (with cached visibility score) |
| `GET` | `/sky/satellites/visible` | user | Satellites currently visible from a location |
| `GET` | `/sky/focus` | user | Focused sky view for a direction/location |
| `GET` | `/starmap/` | user | Star map data for a lat/lon |
| `GET` | `/constellations/` | user | All constellations with mythology |
| `GET` | `/lessons/` | user | List astronomy lessons |
| `GET` | `/lessons/{id}` | user | Single lesson with full content |
| `GET` | `/lessons/by-category/{category}` | user | Lessons filtered by category |
| `GET` | `/quiz/` | user | Quiz questions |
| `POST` | `/quiz/submit` | user | Submit quiz answers and receive a score |
| `GET` | `/quiz/history` | user | Past quiz submissions |
| `GET` | `/watchlist/` | user | User's star watchlist |
| `POST` | `/watchlist/` | user | Add an object to the watchlist |
| `GET` | `/user/settings/` | user | Current notification/UI preferences |
| `PATCH` | `/user/settings/` | user | Update preferences |
| `POST` | `/jwst/search` | Pro/Premium | Free-text search for JWST imagery of a target |
| `POST` | `/jwst/images` | Pro/Premium | Request a MAST product be downloaded and processed |
| `GET` | `/jwst/images/{id}` | Pro/Premium | Poll a request's status |
| `GET` | `/jwst/images` | Pro/Premium | List current user's JWST requests |
| `GET` | `/payments/plans` | -- | Available subscription plans |
| `GET` | `/payments/subscription` | user | Current subscription status |
| `GET` | `/payments/transactions` | user | Payment history |
| `POST` | `/payments/checkout` | user | Start a Stripe/Paystack checkout |
| `POST` | `/payments/verify` | user | Verify a completed payment |
| `POST` | `/payments/webhook` | -- | Stripe webhook receiver |
| `POST` | `/payments/mpesa/stk-push` | user | Initiate an M-Pesa STK push |
| `POST` | `/payments/mpesa/callback` | -- | M-Pesa callback receiver |
| `POST` | `/payments/cancel` | user | Cancel current subscription |

> `satellites.py` and `sky_routes.py` both register under the `/sky` prefix, and `celestial.py` and `events.py` both register under `/events` -- intentional, each router owns different sub-paths, documented above.

---

## External APIs & Data Sources

| Service | Purpose | Cost |
|---|---|---|
| [CelesTrak](https://celestrak.org) | TLE orbital data for 20,000+ satellites | Free |
| [MAST Archive](https://mast.stsci.edu/) (via `astroquery`) | Public James Webb Space Telescope mosaic imagery | Free |
| [AstronomyAPI](https://astronomyapi.com) | Constellation/body positions, rise-set times, live events | Free tier |
| [OpenWeather](https://openweathermap.org/api) | Cloud cover for stargazing visibility scores | Free tier |
| [Open Notify](http://open-notify.org) | ISS real-time position | Free |
| [N2YO](https://www.n2yo.com/api/) | Satellite tracking | Free tier |
| [NASA APIs](https://api.nasa.gov) | Reserved for future use (APOD, NEO, etc.) | Free |
| [OpenStreetMap Nominatim](https://nominatim.org/) | Reverse geocoding for saved locations | Free (rate-limited) |
| Stripe / M-Pesa Daraja / Paystack | Subscription payments | Transaction fees apply |

---

## Database Schema

All tables managed via Alembic migrations in `backend/alembic/versions/`.

| Table | Purpose |
|---|---|
| `users` | User accounts and hashed credentials |
| `user_settings` | Per-user preferences, including `notifications_enabled` |
| `user_subscriptions` | Free / Pro / Premium plan and billing status |
| `transactions` | Payment history (Stripe, M-Pesa, Paystack) |
| `lessons` | Astronomy 101 lesson content |
| `quiz_questions` / `quiz_answers` | Quiz question bank |
| `quiz_submissions` | User quiz attempts and scores |
| `location_entries` | Saved observing locations: lat/lon, reverse-geocoded city/country, cached `visibility_score` |
| `star_watchlist` | User-saved stars and constellations |
| `astronomer_quotes` | Quote bank |
| `solar_events` | Meteor showers and eclipses: timing, ZHR, radiant, visibility latitude range |
| `notifications` | In-app alert feed, one row per (user, solar_event) pair, idempotent |
| `jwst_requests` | JWST search-to-preview pipeline state per user request |

Run `alembic upgrade head` to apply all migrations.
Run `alembic downgrade -1` to roll back one step.

---

## AR Coordinate System

The AR star map pipeline runs every frame at ~30fps:

```
GPS + IMU sensors + UTC time
        |
        v
Device orientation matrix
(SensorManager TYPE_ROTATION_VECTOR -- fuses accel + gyro + compass)
        |
        v
Local Sidereal Time (LST)
LST = Greenwich Mean Sidereal Time + longitude offset
        |
        v
RA / Dec  ->  Altitude / Azimuth
Hour Angle (HA) = LST - Right Ascension
sin(Alt) = sin(Dec)sin(Lat) + cos(Dec)cos(Lat)cos(HA)
        |
        v
Alt/Az -> camera-relative 3D vector (apply device rotation matrix)
        |
        v
Perspective projection -> screen pixel (x, y)
(FOV + screen dimensions)
        |
        v
Canvas / OpenGL AR overlay render
(magnitude filter: hide stars dimmer than mag 5.0 in dense sky regions)
```

Stars behind the device (negative z after rotation) are culled before projection. The coordinate math lives in `backend/app/controllers/skyController.py`, which also now implements moon phase, rise/set, planet positions, ISS tracking, and visibility scoring -- it is no longer an empty placeholder (see [Known Issues](#known-issues) for what is still accurate from the original list). The client-side renderer is `ar/SkyOverlayRenderer.kt`; this session did not audit its current state.

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

Audio is managed by `SoundManager` -- `SoundPool` for low-latency SFX, `ExoPlayer` for streamed ambient tracks. Not audited this session.

---

## Roadmap

### Completed
- [x] User auth (signup / login / JWT, profile, admin role management)
- [x] Database schema and Alembic migrations
- [x] Constellation data (88 constellations with mythology)
- [x] Quiz system (question bank, submission + history)
- [x] Lesson content, filterable by category
- [x] `skyController.py` -- moon phase, rise/set, visibility score, planet positions, ISS, AR scene endpoint
- [x] Satellite TLE fetch + cache (CelesTrak, refreshed every 6h via Celery Beat)
- [x] Celestial event data (seeded meteor showers + verified eclipse dates) and daily alert scan
- [x] In-app notification feed (list, unread count, mark read)
- [x] Location save/history, with reverse geocoding and cached visibility scores (refreshed every 3h)
- [x] JWST premium feature: MAST search, background download, FITS-to-preview rendering pipeline
- [x] Subscriptions & payments: Stripe, M-Pesa STK push, Paystack, webhook/callback handling

### In Progress / Not Yet Audited
- [ ] AR canvas overlay renderer in Kotlin (star projection) -- status unknown, needs re-verification against current `frontend/`
- [ ] Star catalog integration (Hipparcos / Yale BSC) for the AR overlay
- [ ] `build.gradle.kts` Groovy/KTS dependency issue -- needs re-verification

### Planned
- [ ] Full night mode (red-tinted UI for dark-sky preservation)
- [ ] Flashcard mode for lessons
- [ ] Offline mode for lessons and star catalog
- [ ] Localization -- Swahili (sw) support
- [ ] Google Play Store release
- [ ] Consolidate the two competing weather/visibility implementations (see Known Issues)
- [ ] Fix `requirements.txt` encoding (see Known Issues)

---

## Known Issues

| Issue | Status |
|---|---|
| `backend/requirements.txt` is saved as UTF-16 instead of UTF-8 -- `pip` and Docker builds work fine, but git treats the file as binary, so diffs are unreadable | Needs fix |
| Two separate `get_visibility_forecast` implementations exist (`app/utils/astronomy.py`, OpenWeather-based and complete; `app/utils/weather.py`, weatherapi.com-based and missing cloud-cover data) -- `/events/night-sky` currently uses the incomplete one | Needs consolidation |
| `satellites.py` and `sky_routes.py` share the `/sky` prefix; `celestial.py` and `events.py` share `/events` -- not broken, but easy to misread as a conflict | Documented above, consider renaming prefixes for clarity |
| `AndroidManifest.xml` missing `INTERNET` permission declaration | Not re-verified this session |
| `SoundManager` referenced a nested resource path `R.raw.ui.galaxy_tap` -- Android does not support subdirectory raw resources | Not re-verified this session |

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
> -- Carl Sagan