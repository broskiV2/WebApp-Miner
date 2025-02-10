import os
import logging
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

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

# Initialisation de Flask
app = Flask(__name__)
CORS(app)  # Activation de CORS pour permettre les requêtes depuis GitHub Pages

# Initialisation du bot Telegram
telegram_app = Application.builder().token(TOKEN).build()

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

# Ajout des handlers
telegram_app.add_handler(CommandHandler("start", start))

# Route pour le webhook Telegram
@app.route(f'/webhook/{TOKEN}', methods=['POST'])
async def webhook():
    """Endpoint pour recevoir les mises à jour de Telegram"""
    try:
        logger.info("Mise à jour reçue via webhook")
        update = Update.de_json(request.get_json(), telegram_app.bot)
        await telegram_app.process_update(update)
        return 'OK'
    except Exception as e:
        logger.error(f"Erreur dans le webhook: {str(e)}")
        return 'Error', 500

# Route pour configurer le webhook
@app.route('/set-webhook')
async def set_webhook():
    """Configure le webhook pour le bot"""
    try:
        webhook_url = f"{BASE_URL}/webhook/{TOKEN}"
        await telegram_app.bot.delete_webhook()  # Supprime l'ancien webhook
        await telegram_app.bot.set_webhook(webhook_url)
        webhook_info = await telegram_app.bot.get_webhook_info()
        logger.info(f"Webhook configuré sur {webhook_url}")
        return jsonify({
            "status": "Webhook set",
            "url": webhook_url,
            "webhook_info": {
                "url": webhook_info.url,
                "has_custom_certificate": webhook_info.has_custom_certificate,
                "pending_update_count": webhook_info.pending_update_count,
                "last_error_date": webhook_info.last_error_date,
                "last_error_message": webhook_info.last_error_message
            }
        })
    except Exception as e:
        logger.error(f"Erreur lors de la configuration du webhook: {str(e)}")
        return jsonify({"status": "Error", "error": str(e)}), 500

# Route API pour le solde
@app.route('/')
def home():
    return jsonify({
        "status": "Server is running",
        "webhook_info": f"{BASE_URL}/set-webhook"
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