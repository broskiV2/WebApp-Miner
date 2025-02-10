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
@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook():
    """Endpoint pour recevoir les mises à jour de Telegram"""
    try:
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
        webhook_url = f"https://{request.host}/{TOKEN}"
        await telegram_app.bot.set_webhook(webhook_url)
        logger.info(f"Webhook configuré sur {webhook_url}")
        return jsonify({"status": "Webhook set", "url": webhook_url})
    except Exception as e:
        logger.error(f"Erreur lors de la configuration du webhook: {str(e)}")
        return jsonify({"status": "Error", "error": str(e)}), 500

# Route API pour le solde
@app.route('/')
def home():
    return jsonify({
        "status": "Server is running",
        "webhook_url": f"https://{request.host}/{TOKEN}"
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