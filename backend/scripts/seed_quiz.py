"""
Seed the quiz_questions table. Idempotent: skips questions that already exist.

Run:  docker exec eyesky_api python -m scripts.seed_quiz
"""
import json
import os
import random

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models.quiz import QuizQuestion

# (difficulty, topic, question, correct answer, [three wrong answers])
QUESTIONS = [
    ("simple", "planets", "Which planet is closest to the Sun?", "Mercury", ["Venus", "Mars", "Earth"]),
    ("simple", "planets", "Which planet is the largest in our Solar System?", "Jupiter", ["Saturn", "Neptune", "Earth"]),
    ("simple", "planets", "Which planet is known as the Red Planet?", "Mars", ["Venus", "Mercury", "Jupiter"]),
    ("simple", "planets", "How many planets are in our Solar System?", "8", ["7", "9", "10"]),
    ("simple", "planets", "Which planet has the most prominent ring system?", "Saturn", ["Mars", "Mercury", "Venus"]),
    ("simple", "planets", "Which planet is the hottest, thanks to its thick carbon dioxide atmosphere?", "Venus", ["Mercury", "Mars", "Jupiter"]),
    ("simple", "planets", "What causes the seasons on Earth?", "The tilt of Earth's axis", ["Earth's distance from the Sun", "The Moon's gravity", "Solar flares"]),
    ("simple", "moon", "About how long does the Moon take to orbit the Earth?", "About one month", ["About one day", "About one week", "About one year"]),
    ("simple", "stars", "What is the closest star to Earth?", "The Sun", ["Sirius", "Alpha Centauri", "Polaris"]),
    ("simple", "stars", "Which star is the brightest in Earth's night sky?", "Sirius", ["Polaris", "Betelgeuse", "Vega"]),
    ("simple", "stars", "What is the name of the North Star?", "Polaris", ["Sirius", "Vega", "Rigel"]),
    ("simple", "constellations", "The Big Dipper is part of which constellation?", "Ursa Major", ["Orion", "Cassiopeia", "Scorpius"]),
    ("simple", "constellations", "How many bright stars make up Orion's Belt?", "Three", ["Two", "Four", "Five"]),
    ("simple", "cosmology", "What is the name of our home galaxy?", "The Milky Way", ["Andromeda", "Triangulum", "Whirlpool"]),
    ("simple", "cosmology", "What does a light-year measure?", "Distance", ["Time", "Speed", "Brightness"]),
    ("simple", "meteors", "What is a 'shooting star' actually?", "A meteoroid burning up in Earth's atmosphere", ["A star falling to Earth", "A comet's tail", "A distant supernova"]),
    ("simple", "exploration", "Who was the first human to walk on the Moon?", "Neil Armstrong", ["Buzz Aldrin", "Yuri Gagarin", "John Glenn"]),
    ("simple", "exploration", "Which dwarf planet did NASA's New Horizons spacecraft fly past in 2015?", "Pluto", ["Ceres", "Eris", "Haumea"]),
    ("complex", "cosmology", "Roughly how old is the universe?", "13.8 billion years", ["4.6 billion years", "1.4 billion years", "46 billion years"]),
    ("complex", "cosmology", "What does the Hubble constant describe?", "The rate at which the universe is expanding", ["The mass of the Milky Way", "The speed of light in a vacuum", "The age of the oldest stars"]),
    ("complex", "cosmology", "Approximately how fast does light travel in a vacuum?", "About 300,000 km/s", ["About 30,000 km/s", "About 3,000 km/s", "About 3,000,000 km/s"]),
    ("complex", "stars", "What will the Sun become after its red giant phase?", "A white dwarf", ["A neutron star", "A black hole", "A pulsar"]),
    ("complex", "stars", "Approximately what is the Chandrasekhar limit, the maximum mass of a white dwarf?", "About 1.4 solar masses", ["About 0.5 solar masses", "About 3 solar masses", "About 8 solar masses"]),
    ("complex", "stars", "Which spectral class contains the hottest stars?", "O", ["M", "G", "K"]),
    ("complex", "stars", "Which bright star in Orion is a red supergiant?", "Betelgeuse", ["Rigel", "Bellatrix", "Sirius"]),
    ("complex", "deep sky", "Which Messier object is the Andromeda Galaxy?", "M31", ["M1", "M13", "M42"]),
    ("complex", "planets", "Which planet has the shortest day, rotating once in under 10 hours?", "Jupiter", ["Earth", "Mars", "Saturn"]),
    ("complex", "planets", "Which planet's axis is tilted so far that it rotates almost on its side?", "Uranus", ["Neptune", "Saturn", "Jupiter"]),
    ("complex", "moons", "Which moon of Saturn has a thick nitrogen atmosphere and lakes of liquid methane?", "Titan", ["Enceladus", "Mimas", "Rhea"]),
    ("complex", "black holes", "What is the boundary around a black hole beyond which nothing can escape?", "The event horizon", ["The photon sphere", "The accretion disk", "The ergosphere"]),
    ("complex", "exploration", "Where is the James Webb Space Telescope located?", "The Sun-Earth L2 point, about 1.5 million km from Earth", ["In low Earth orbit", "On the far side of the Moon", "At the Sun-Earth L1 point"]),
    ("complex", "exploration", "Why does the James Webb Space Telescope observe in infrared?", "Light from the most distant galaxies is stretched into the infrared by cosmic expansion", ["Infrared light is brighter than visible light", "Visible light cannot travel through space", "Infrared cameras are cheaper to build"]),
]


def main() -> None:
    url = os.getenv("DATABASE_URL_SYNC") or os.environ["DATABASE_URL"].replace("+asyncpg", "")
    engine = create_engine(url)
    added = 0
    with Session(engine) as db:
        existing = set(db.execute(select(QuizQuestion.question_text)).scalars().all())
        for difficulty, topic, text, correct, wrong in QUESTIONS:
            if text in existing:
                continue
            options = [correct] + wrong
            random.Random(text).shuffle(options)  # stable, but correct answer is not always first
            db.add(QuizQuestion(
                question_text=text,
                options=json.dumps(options),
                correct_answer=correct,
                difficulty=difficulty,
                topic=topic,
            ))
            added += 1
        db.commit()
    print(f"Seeded {added} new questions ({len(QUESTIONS) - added} already present).")


if __name__ == "__main__":
    main()