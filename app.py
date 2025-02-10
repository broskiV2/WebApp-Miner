import os
import logging
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest
import json
import asyncio
from functools import wraps
from datetime import datetime, timedelta
from models import db, User, MiningPlan, Transaction, MiningStats, default_plans

# Configuration des logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://broskiv2.github.io/WebApp-Miner')
BASE_URL = os.getenv('BASE_URL', 'https://webapp-miner.onrender.com')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')

# Configuration de la boucle d'événements
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Initialisation de Flask
app = Flask(__name__)
CORS(app)  # Activation de CORS pour permettre les requêtes depuis GitHub Pages

# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Configuration du request pour le bot avec un pool plus grand
request_handler = HTTPXRequest(connection_pool_size=8)

# Initialisation du bot Telegram avec le request configuré
bot = Bot(token=TOKEN, request=request_handler)
telegram_app = Application.builder().token(TOKEN).request(request_handler).build()

def async_route(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(f(*args, **kwargs))
    return decorated_function

# Commandes du bot Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande de démarrage avec bouton pour ouvrir la webapp"""
    try:
        user = update.effective_user
        logger.info(f"Commande /start reçue de {user.id} ({user.first_name})")
        
        keyboard = [[KeyboardButton(
            text="Ouvrir le Miner",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Création ou mise à jour de l'utilisateur dans la base de données
        try:
            with app.app_context():
                db_user = User.query.filter_by(telegram_id=user.id).first()
                if not db_user:
                    db_user = User(
                        telegram_id=user.id,
                        username=user.username,
                        first_name=user.first_name
                    )
                    db.session.add(db_user)
                    db.session.commit()
                    logger.info(f"Nouvel utilisateur créé: {user.id}")
        except Exception as db_error:
            logger.error(f"Erreur base de données: {str(db_error)}")
            # On continue même si la BD échoue pour au moins montrer le bouton
        
        await update.message.reply_text(
            f"Bienvenue {user.first_name} sur WeMine! Cliquez sur le bouton ci-dessous pour commencer:",
            reply_markup=reply_markup
        )
        logger.info("Message de bienvenue envoyé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la commande start: {str(e)}")
        # En cas d'erreur, on essaie quand même d'envoyer un message basique
        try:
            await update.message.reply_text(
                "Bienvenue sur WeMine! Cliquez sur le bouton ci-dessous pour commencer:",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton(
                    text="Ouvrir le Miner",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )]], resize_keyboard=True)
            )
        except Exception as msg_error:
            logger.error(f"Erreur lors de l'envoi du message de secours: {str(msg_error)}")

# Ajout des handlers
telegram_app.add_handler(CommandHandler("start", start))

# Route pour le webhook Telegram
@app.route(f'/webhook/{TOKEN}', methods=['POST'])
@async_route
async def webhook():
    """Endpoint pour recevoir les mises à jour de Telegram"""
    try:
        logger.info("Mise à jour reçue via webhook")
        data = request.get_json()
        logger.info(f"Données reçues: {json.dumps(data, indent=2)}")
        
        update = Update.de_json(data, bot)
        await telegram_app.initialize()
        await telegram_app.process_update(update)
        return 'OK'
    except Exception as e:
        logger.error(f"Erreur dans le webhook: {str(e)}")
        return 'Error', 500

# Routes API
@app.route('/api/user/<int:telegram_id>')
def get_user_info(telegram_id):
    """Récupère les informations de l'utilisateur"""
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    return jsonify({
        "id": user.telegram_id,
        "username": user.username,
        "balance": user.balance,
        "active_plan": user.active_plan.name if user.active_plan else None,
        "mining_rate": user.active_plan.mining_rate if user.active_plan else 0
    })

@app.route('/api/plans')
def get_mining_plans():
    """Récupère la liste des plans de minage disponibles"""
    plans = MiningPlan.query.all()
    return jsonify([{
        "id": plan.id,
        "name": plan.name,
        "description": plan.description,
        "price": plan.price,
        "mining_rate": plan.mining_rate,
        "duration": plan.duration
    } for plan in plans])

@app.route('/api/transactions/<int:telegram_id>')
def get_user_transactions(telegram_id):
    """Récupère l'historique des transactions de l'utilisateur"""
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.created_at.desc()).all()
    return jsonify([{
        "type": tx.type,
        "amount": tx.amount,
        "status": tx.status,
        "created_at": tx.created_at.isoformat()
    } for tx in transactions])

@app.route('/api/mining/stats/<int:telegram_id>')
def get_mining_stats(telegram_id):
    """Récupère les statistiques de minage de l'utilisateur"""
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    active_stats = MiningStats.query.filter_by(user_id=user.id, is_active=True).first()
    if not active_stats:
        return jsonify({
            "is_mining": False,
            "total_mined": 0,
            "mining_rate": 0,
            "time_remaining": 0
        })
    
    time_remaining = (active_stats.end_date - datetime.utcnow()).days
    return jsonify({
        "is_mining": True,
        "total_mined": active_stats.total_mined,
        "mining_rate": active_stats.mining_rate,
        "time_remaining": max(0, time_remaining)
    })

@app.route('/api/mining/start', methods=['POST'])
def start_mining():
    """Démarre le minage pour un utilisateur"""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    plan_id = data.get('plan_id')
    
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    plan = MiningPlan.query.get(plan_id)
    if not plan:
        return jsonify({"error": "Plan non trouvé"}), 404
    
    if user.balance < plan.price:
        return jsonify({"error": "Solde insuffisant"}), 400
    
    # Déduire le coût du plan
    user.balance -= plan.price
    user.active_plan_id = plan.id
    user.plan_activation_date = datetime.utcnow()
    
    # Créer les statistiques de minage
    stats = MiningStats(
        user_id=user.id,
        plan_id=plan.id,
        mining_rate=plan.mining_rate,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=plan.duration)
    )
    
    # Enregistrer la transaction
    transaction = Transaction(
        user_id=user.id,
        type='mining_activation',
        amount=-plan.price,
        status='completed'
    )
    
    db.session.add(stats)
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Minage démarré avec succès"})

@app.route('/api/deposit', methods=['POST'])
def deposit():
    """Traite un dépôt"""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    amount = data.get('amount')
    tx_hash = data.get('tx_hash')
    
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    transaction = Transaction(
        user_id=user.id,
        type='deposit',
        amount=amount,
        status='pending',
        tx_hash=tx_hash
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Dépôt en attente de confirmation",
        "transaction_id": transaction.id
    })

@app.route('/api/withdraw', methods=['POST'])
def withdraw():
    """Traite un retrait"""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    amount = data.get('amount')
    address = data.get('address')
    
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    if user.balance < amount:
        return jsonify({"error": "Solde insuffisant"}), 400
    
    transaction = Transaction(
        user_id=user.id,
        type='withdrawal',
        amount=-amount,
        status='pending'
    )
    
    user.balance -= amount
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Retrait en cours de traitement",
        "transaction_id": transaction.id
    })

# Routes existantes pour le webhook
@app.route('/set-webhook')
@async_route
async def set_webhook():
    """Configure le webhook pour le bot"""
    try:
        webhook_url = f"{BASE_URL}/webhook/{TOKEN}"
        await bot.delete_webhook()
        await bot.set_webhook(webhook_url)
        webhook_info = await bot.get_webhook_info()
        return jsonify({
            "status": "Webhook set",
            "url": webhook_url,
            "webhook_info": webhook_info.to_dict()
        })
    except Exception as e:
        logger.error(f"Erreur lors de la configuration du webhook: {str(e)}")
        return jsonify({"status": "Error", "error": str(e)}), 500

@app.route('/bot-info')
@async_route
async def bot_info():
    """Vérifie le statut du bot"""
    try:
        bot_info = await bot.get_me()
        webhook_info = await bot.get_webhook_info()
        return jsonify({
            "status": "Bot is running",
            "bot_info": {
                "id": bot_info.id,
                "name": bot_info.first_name,
                "username": bot_info.username,
                "can_join_groups": bot_info.can_join_groups,
                "can_read_all_group_messages": bot_info.can_read_all_group_messages,
                "supports_inline_queries": bot_info.supports_inline_queries
            },
            "webhook_info": webhook_info.to_dict()
        })
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du bot: {str(e)}")
        return jsonify({"status": "Error", "error": str(e)}), 500

@app.route('/reset-webhook')
@async_route
async def reset_webhook():
    """Réinitialise complètement le webhook"""
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await asyncio.sleep(2)
        webhook_url = f"{BASE_URL}/webhook/{TOKEN}"
        await bot.set_webhook(webhook_url)
        webhook_info = await bot.get_webhook_info()
        return jsonify({
            "status": "Webhook reset successful",
            "webhook_info": webhook_info.to_dict()
        })
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation du webhook: {str(e)}")
        return jsonify({"status": "Error", "error": str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        "status": "Server is running",
        "endpoints": {
            "webhook_setup": f"{BASE_URL}/set-webhook",
            "webhook_reset": f"{BASE_URL}/reset-webhook",
            "bot_info": f"{BASE_URL}/bot-info",
            "api": {
                "user": "/api/user/<telegram_id>",
                "plans": "/api/plans",
                "transactions": "/api/transactions/<telegram_id>",
                "mining_stats": "/api/mining/stats/<telegram_id>",
                "mining_start": "/api/mining/start",
                "deposit": "/api/deposit",
                "withdraw": "/api/withdraw"
            }
        }
    })

# Initialisation de la base de données
def init_db():
    try:
        with app.app_context():
            db.create_all()
            
            # Ajout des plans par défaut s'ils n'existent pas
            if MiningPlan.query.count() == 0:
                for plan_data in default_plans:
                    plan = MiningPlan(**plan_data)
                    db.session.add(plan)
                db.session.commit()
                logger.info("Plans de minage par défaut créés avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")

# Initialiser la base de données au démarrage
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 