🌌 Astronomy App – System Architecture Overview

┌────────────────────────────────────────────────────────────────────────────┐
│                            🌠 Mobile Frontend (React Native)               │
│                                                                            │
│   - AR Star Map UI                                                         │
│   - Astronomy 101 Lessons                                                  │
│   - Quizzes and Flashcards                                                 │
│   - Celestial Event Alerts                                                 │
│   - Satellite Map Viewer                                                   │
│                                                                            │
│   📡 Calls APIs via HTTPS                                                  │
└────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│      🌐 Node.js Backend (Express / Fastify)   │
│                                              │
│  - REST API for mobile frontend              │
│  - Auth, quizzes, lessons, user data         │
│  - Caching & rate limiting (optional)        │
│  - Calls Python microservice for TLE logic   │
│  - Calls external APIs (weather, ISS, NASA)  │
└──────────────────────────────────────────────┘
        │                          │
        ▼                          ▼
┌────────────────────────────┐    ┌────────────────────────────────────┐
│  🐘 PostgreSQL Database     │    │ 🐍 Python Microservice (TLE/Space) │
│                            │    │                                    │
│  - Users                   │    │ - TLE parsing (from NORAD)         │
│  - Quiz & Lesson Content   │    │ - Satellite position calculations  │
│  - Celestial Event Logs    │    │ - Ephemeris, visibility scores     │
│  - Saved Progress          │    │ - Can expose simple REST endpoints │
└────────────────────────────┘    └────────────────────────────────────┘
                                         ▲
                                         │
                          ┌───────────────────────────────┐
                          │ 🔭 External APIs               │
                          │ - OpenWeather / WeatherAPI     │
                          │ - Open Notify (ISS Tracker)    │
                          │ - NASA APIs                    │
                          │ - Celestrak / NORAD TLE Feeds  │
                          └───────────────────────────────┘
