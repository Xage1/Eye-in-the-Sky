"""
Seeds the astronomer_quotes table with 30 famous astronomy quotes.
Run inside Docker: docker-compose exec api python -m app.scripts.seed_quotes
"""

import asyncio
import logging
from sqlalchemy.future import select
from app.database import SessionLocal
from app.models.quote import AstronomerQuote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUOTES = [
    {"quote": "The cosmos is within us. We are made of star-stuff. We are a way for the universe to know itself.", "astronomer": "Carl Sagan", "birth_year": 1934, "death_year": 1996, "nationality": "American", "category": "universe", "featured": True},
    {"quote": "Somewhere, something incredible is waiting to be known.", "astronomer": "Carl Sagan", "birth_year": 1934, "death_year": 1996, "nationality": "American", "category": "exploration", "featured": True},
    {"quote": "The universe is under no obligation to make sense to you.", "astronomer": "Neil deGrasse Tyson", "birth_year": 1958, "nationality": "American", "category": "universe", "featured": True},
    {"quote": "We are all connected; to each other, biologically. To the earth, chemically. To the rest of the universe atomically.", "astronomer": "Neil deGrasse Tyson", "birth_year": 1958, "nationality": "American", "category": "stars", "featured": True},
    {"quote": "The important thing is not to stop questioning. Curiosity has its own reason for existing.", "astronomer": "Albert Einstein", "birth_year": 1879, "death_year": 1955, "nationality": "German-American", "category": "exploration", "featured": True},
    {"quote": "Look up at the stars and not down at your feet. Try to make sense of what you see, and wonder about what makes the universe exist.", "astronomer": "Stephen Hawking", "birth_year": 1942, "death_year": 2018, "nationality": "British", "category": "stars", "featured": True},
    {"quote": "We are just an advanced breed of monkeys on a minor planet of a very average star. But we can understand the universe. That makes us something very special.", "astronomer": "Stephen Hawking", "birth_year": 1942, "death_year": 2018, "nationality": "British", "category": "universe"},
    {"quote": "The nitrogen in our DNA, the calcium in our teeth, the iron in our blood, the carbon in our apple pies were made in the interiors of collapsing stars.", "astronomer": "Carl Sagan", "birth_year": 1934, "death_year": 1996, "nationality": "American", "category": "stars"},
    {"quote": "In the beginning there was nothing, which exploded.", "astronomer": "Terry Pratchett", "birth_year": 1948, "death_year": 2015, "nationality": "British", "category": "universe"},
    {"quote": "Space is big. Really big. You just won't believe how vastly, hugely, mind-bogglingly big it is.", "astronomer": "Douglas Adams", "birth_year": 1952, "death_year": 2001, "nationality": "British", "category": "universe"},
    {"quote": "To confine our attention to terrestrial matters would be to limit the human spirit.", "astronomer": "Stephen Hawking", "birth_year": 1942, "death_year": 2018, "nationality": "British", "category": "exploration"},
    {"quote": "The sky is the limit only for those who aren't afraid to fly.", "astronomer": "Bob Bello", "nationality": "American", "category": "exploration"},
    {"quote": "Astronomy compels the soul to look upward, and leads us from this world to another.", "astronomer": "Plato", "birth_year": -428, "death_year": -348, "nationality": "Greek", "category": "stars", "featured": True},
    {"quote": "The most beautiful thing we can experience is the mysterious. It is the source of all true art and science.", "astronomer": "Albert Einstein", "birth_year": 1879, "death_year": 1955, "nationality": "German-American", "category": "universe"},
    {"quote": "There are no passengers on spaceship earth. We are all crew.", "astronomer": "Marshall McLuhan", "birth_year": 1911, "death_year": 1980, "nationality": "Canadian", "category": "exploration"},
    {"quote": "Every atom in your body came from a star that exploded. And the atoms in your left hand probably came from a different star than your right hand.", "astronomer": "Lawrence Krauss", "birth_year": 1954, "nationality": "American", "category": "stars"},
    {"quote": "When you look at the stars and the galaxy, you feel that you are not just from any particular piece of land, but from the solar system.", "astronomer": "Kalpana Chawla", "birth_year": 1961, "death_year": 2003, "nationality": "Indian-American", "category": "exploration"},
    {"quote": "I would rather be ashes than dust! I would rather my spark should burn out in a brilliant blaze than it should be stifled by dry-rot.", "astronomer": "Jack London", "birth_year": 1876, "death_year": 1916, "nationality": "American", "category": "exploration"},
    {"quote": "The universe is not required to be in perfect harmony with human ambition.", "astronomer": "Carl Sagan", "birth_year": 1934, "death_year": 1996, "nationality": "American", "category": "universe"},
    {"quote": "Not only do we live among the stars, the stars live within us.", "astronomer": "Neil deGrasse Tyson", "birth_year": 1958, "nationality": "American", "category": "stars", "featured": True},
    {"quote": "Man must rise above the Earth — to the top of the atmosphere and beyond — for only thus will he fully understand the world in which he lives.", "astronomer": "Socrates", "birth_year": -470, "death_year": -399, "nationality": "Greek", "category": "exploration"},
    {"quote": "The sun, with all the planets revolving around it and depending on it, can still ripen a bunch of grapes as if it had nothing else in the universe to do.", "astronomer": "Galileo Galilei", "birth_year": 1564, "death_year": 1642, "nationality": "Italian", "category": "stars", "featured": True},
    {"quote": "Equipped with his five senses, man explores the universe around him and calls the adventure science.", "astronomer": "Edwin Hubble", "birth_year": 1889, "death_year": 1953, "nationality": "American", "category": "exploration", "featured": True},
    {"quote": "The universe is a pretty big place. If it's just us, seems like an awful waste of space.", "astronomer": "Carl Sagan", "birth_year": 1934, "death_year": 1996, "nationality": "American", "category": "universe"},
    {"quote": "Once you can accept the universe as matter expanding into nothing that is something, wearing stripes with plaid comes easy.", "astronomer": "Albert Einstein", "birth_year": 1879, "death_year": 1955, "nationality": "German-American", "category": "universe"},
    {"quote": "Science is not only compatible with spirituality; it is a profound source of spirituality.", "astronomer": "Carl Sagan", "birth_year": 1934, "death_year": 1996, "nationality": "American", "category": "universe"},
    {"quote": "The stars are the land-marks of the universe.", "astronomer": "John Herschel", "birth_year": 1792, "death_year": 1871, "nationality": "British", "category": "stars"},
    {"quote": "Across the sea of space, the stars are other suns.", "astronomer": "Carl Sagan", "birth_year": 1934, "death_year": 1996, "nationality": "American", "category": "stars"},
    {"quote": "Two things are infinite: the universe and human stupidity; and I'm not sure about the universe.", "astronomer": "Albert Einstein", "birth_year": 1879, "death_year": 1955, "nationality": "German-American", "category": "universe"},
    {"quote": "To carry the news of the sky is perhaps the oldest profession, and the first necessity of civilization.", "astronomer": "Harlow Shapley", "birth_year": 1885, "death_year": 1972, "nationality": "American", "category": "stars"},
]


async def seed():
    async with SessionLocal() as db:
        result = await db.execute(select(AstronomerQuote).limit(1))
        if result.scalars().first():
            logger.info("Quotes already seeded — skipping")
            return

        for q in QUOTES:
            db.add(AstronomerQuote(
                quote=q["quote"],
                astronomer=q["astronomer"],
                birth_year=q.get("birth_year"),
                death_year=q.get("death_year"),
                nationality=q.get("nationality"),
                category=q.get("category"),
                featured=q.get("featured", False),
            ))

        await db.commit()
        logger.info("Seeded %d astronomer quotes", len(QUOTES))


if __name__ == "__main__":
    asyncio.run(seed())