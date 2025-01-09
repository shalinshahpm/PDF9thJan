import os
import logging
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = '/tmp'  # Temporary storage

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    with app.app_context():
        # Import models
        from models import User, PDFFile

        # Import blueprints
        from blueprints.auth import auth_bp
        from blueprints.pdf import pdf_bp
        from blueprints.subscription import subscription_bp

        # Register blueprints
        app.register_blueprint(auth_bp)
        app.register_blueprint(pdf_bp)
        app.register_blueprint(subscription_bp)

        # Create database tables
        db.create_all()

        # Root route
        @app.route('/')
        def index():
            if current_user.is_authenticated:
                return redirect(url_for('pdf.operations'))
            return redirect(url_for('auth.login'))

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

    return app