import os
import logging
import asyncio
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from threading import Thread

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

# Vérification du token
if not TOKEN:
    logger.error("TELEGRAM_TOKEN n'est pas défini!")
else:
    logger.info(f"Token trouvé: {TOKEN[:5]}...")

# Variable globale pour l'application Telegram
telegram_app = None

# Initialisation de Flask
app = Flask(__name__)
CORS(app)  # Activation de CORS pour permettre les requêtes depuis GitHub Pages

async def start_telegram_bot():
    """Démarrage du bot Telegram"""
    try:
        global telegram_app
        if telegram_app is None:
            logger.info("Démarrage du bot Telegram...")
            telegram_app = Application.builder().token(TOKEN).build()
            telegram_app.add_handler(CommandHandler("start", start))
            logger.info("Bot configuré, démarrage du polling...")
            await telegram_app.initialize()
            await telegram_app.start()
            await telegram_app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {str(e)}")
        raise

# Route API pour le solde
@app.route('/')
def home():
    status = "Bot running" if telegram_app else "Bot not running"
    token_status = "Token set" if TOKEN else "No token"
    return jsonify({
        "status": "Server is running",
        "bot_status": status,
        "token_status": token_status
    })

@app.route('/api/balance')
def get_balance():
    return jsonify({
        'balance': 0.00000000,
        'total_pull': 50000,
        'rate': 0.01000000
    })

# Commandes du bot Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande de démarrage avec bouton pour ouvrir la webapp"""
    try:
        logger.info(f"Commande /start reçue de {update.effective_user.id}")
        keyboard = [[KeyboardButton(
            text="Ouvrir le Miner",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Bienvenue sur WeMine! Cliquez sur le bouton ci-dessous pour commencer:",
            reply_markup=reply_markup
        )
        logger.info("Message de bienvenue envoyé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la commande start: {str(e)}")
        raise

@app.route('/start-bot')
def start_bot_endpoint():
    """Endpoint pour démarrer manuellement le bot"""
    try:
        logger.info("Démarrage manuel du bot...")
        asyncio.run(start_telegram_bot())
        return jsonify({"status": "Bot started", "success": True})
    except Exception as e:
        logger.error(f"Erreur lors du démarrage manuel du bot: {str(e)}")
        return jsonify({"status": "Error starting bot", "error": str(e), "success": False})

def create_app():
    try:
        # Démarrage du bot
        logger.info("Démarrage automatique du bot...")
        asyncio.run(start_telegram_bot())
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'application: {str(e)}")
    return app

app = create_app()

if __name__ == '__main__':
    # Démarrage du serveur Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 