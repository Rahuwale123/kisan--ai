from flask import Flask
from flask_caching import Cache
from config import Config
from flask_talisman import Talisman

cache = Cache()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Add security headers
    Talisman(app, force_https=True)
    
    # Initialize cache
    cache.init_app(app, config={
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 300
    })
    
    # Register blueprints
    from app.routes.voice_routes import voice_bp
    app.register_blueprint(voice_bp)
    
    return app 