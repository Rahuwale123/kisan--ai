import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    BASE_URL = os.getenv('BASE_URL', 'http://your-ngrok-url')  
    
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

    DEFAULT_LANGUAGE = 'hi-IN'
    SUPPORTED_LANGUAGES = ['hi-IN', 'mr-IN', 'en-IN']

    WEBHOOK_BASE_URL = os.getenv('BASE_URL')
    if not WEBHOOK_BASE_URL:
        raise ValueError("BASE_URL must be set in environment variables") 
    
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'kisan_db')