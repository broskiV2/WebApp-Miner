from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    balance = db.Column(db.Float, default=0.0)
    active_plan_id = db.Column(db.Integer, db.ForeignKey('mining_plans.id'))
    plan_activation_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relations
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    mining_stats = db.relationship('MiningStats', backref='user', lazy=True)
    active_plan = db.relationship('MiningPlan')

class MiningPlan(db.Model):
    __tablename__ = 'mining_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    mining_rate = db.Column(db.Float, nullable=False)  # USDT par jour
    duration = db.Column(db.Integer, nullable=False)  # Durée en jours
    created_at = db.Column(db.DateTime, default=func.now())

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'deposit', 'withdrawal', 'mining_reward'
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'pending', 'completed', 'failed'
    tx_hash = db.Column(db.String(100))  # Pour les transactions blockchain
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

class MiningStats(db.Model):
    __tablename__ = 'mining_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('mining_plans.id'), nullable=False)
    total_mined = db.Column(db.Float, default=0.0)
    mining_rate = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

# Plans de minage par défaut
default_plans = [
    {
        'name': 'Starter',
        'description': 'Plan de démarrage parfait pour les débutants',
        'price': 50.0,
        'mining_rate': 0.01,
        'duration': 30
    },
    {
        'name': 'Pro',
        'description': 'Pour les mineurs expérimentés',
        'price': 150.0,
        'mining_rate': 0.05,
        'duration': 30
    },
    {
        'name': 'Elite',
        'description': 'Performance maximale pour les professionnels',
        'price': 500.0,
        'mining_rate': 0.2,
        'duration': 30
    }
] 