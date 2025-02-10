from flask import Flask
from flask_migrate import Migrate
from models import db
from app import app

migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 