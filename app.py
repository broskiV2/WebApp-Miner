import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from threading import Thread

# Chargement des variables d'environnement
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://broskiv2.github.io/WebApp-Miner')

# Initialisation de Flask
app = Flask(__name__)
CORS(app)  # Activation de CORS pour permettre les requêtes depuis GitHub Pages

# Variable globale pour l'application Telegram
telegram_app = None

# Route API pour le solde
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
    keyboard = [[KeyboardButton(
        text="Ouvrir le Miner",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Bienvenue sur WeMine! Cliquez sur le bouton ci-dessous pour commencer:",
        reply_markup=reply_markup
    )

def start_telegram_bot():
    """Démarrage du bot Telegram"""
    global telegram_app
    telegram_app = Application.builder().token(TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.run_polling(allowed_updates=Update.ALL_TYPES)

# Démarrage du bot dans un thread au démarrage de l'application
@app.before_first_request
def init_bot():
    thread = Thread(target=start_telegram_bot)
    thread.start()

if __name__ == '__main__':
    # Démarrage du serveur Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 