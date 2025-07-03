import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import Base
from app.models import (
    user,
    location,
    quiz_question,
    quiz_submission,
    quiz_answer,
    user_settings,
    star_watchlist,
    lesson
)
target_metadata = Base.metadata
