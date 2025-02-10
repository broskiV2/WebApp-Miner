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

# Vérification du token
if not TOKEN:
    logger.error("TELEGRAM_TOKEN n'est pas défini!")
else:
    logger.info(f"Token trouvé: {TOKEN[:5]}...")

# Configuration de la boucle d'événements
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Initialisation de Flask
app = Flask(__name__)
CORS(app)  # Activation de CORS pour permettre les requêtes depuis GitHub Pages

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
        
        await update.message.reply_text(
            f"Bienvenue {user.first_name} sur WeMine! Cliquez sur le bouton ci-dessous pour commencer:",
            reply_markup=reply_markup
        )
        logger.info("Message de bienvenue envoyé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la commande start: {str(e)}")
        raise

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

# Route pour configurer le webhook
@app.route('/set-webhook')
@async_route
async def set_webhook():
    """Configure le webhook pour le bot"""
    try:
        webhook_url = f"{BASE_URL}/webhook/{TOKEN}"
        
        # Suppression de l'ancien webhook
        await bot.delete_webhook()
        logger.info("Ancien webhook supprimé")
        
        # Configuration du nouveau webhook
        await bot.set_webhook(webhook_url)
        logger.info(f"Nouveau webhook configuré sur {webhook_url}")
        
        # Vérification de la configuration
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Information du webhook: {webhook_info.to_dict()}")
        
        return jsonify({
            "status": "Webhook set",
            "url": webhook_url,
            "webhook_info": webhook_info.to_dict()
        })
    except Exception as e:
        logger.error(f"Erreur lors de la configuration du webhook: {str(e)}")
        return jsonify({"status": "Error", "error": str(e)}), 500

# Route pour vérifier le statut du bot
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

# Route pour réinitialiser le webhook
@app.route('/reset-webhook')
@async_route
async def reset_webhook():
    """Réinitialise complètement le webhook"""
    try:
        # Suppression du webhook existant
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook supprimé avec succès")
        
        # Attente de 2 secondes
        await asyncio.sleep(2)
        
        # Configuration du nouveau webhook
        webhook_url = f"{BASE_URL}/webhook/{TOKEN}"
        await bot.set_webhook(webhook_url)
        logger.info(f"Nouveau webhook configuré sur {webhook_url}")
        
        # Vérification
        webhook_info = await bot.get_webhook_info()
        
        return jsonify({
            "status": "Webhook reset successful",
            "webhook_info": webhook_info.to_dict()
        })
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation du webhook: {str(e)}")
        return jsonify({"status": "Error", "error": str(e)}), 500

# Route API pour le solde
@app.route('/')
def home():
    return jsonify({
        "status": "Server is running",
        "endpoints": {
            "webhook_setup": f"{BASE_URL}/set-webhook",
            "webhook_reset": f"{BASE_URL}/reset-webhook",
            "bot_info": f"{BASE_URL}/bot-info",
            "balance_api": f"{BASE_URL}/api/balance"
        }
    })

@app.route('/api/balance')
def get_balance():
    return jsonify({
        'balance': 0.00000000,
        'total_pull': 50000,
        'rate': 0.01000000
    })

if __name__ == '__main__':
    # Démarrage du serveur Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 