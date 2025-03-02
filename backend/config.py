import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask settings
SECRET_KEY = 'dev-key-for-development-only'
DEBUG = True

# Data paths
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
USERS_CSV = os.path.join(DATA_DIR, 'users.csv')
PHOTOS_CSV = os.path.join(DATA_DIR, 'photos.csv')
CHAT_HISTORY_CSV = os.path.join(DATA_DIR, 'chat_history.csv')
FRIENDSHIPS_CSV = os.path.join(DATA_DIR, 'friendships.csv')

# Photo storage
PHOTOS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'photos')

# API settings
CORS_HEADERS = 'Content-Type'
