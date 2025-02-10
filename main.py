import os
from dotenv import load_dotenv
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from flask import Flask, render_template, jsonify

# Chargement des variables d'environnement
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL')

# Initialisation de Flask
app = Flask(__name__)

# Routes Flask pour la webapp
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/balance')
def get_balance():
    # Simuler un solde pour l'exemple
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
        web_app=WebAppInfo(url=f"{WEBAPP_URL}")
    )]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Bienvenue sur WeMine! Cliquez sur le bouton ci-dessous pour commencer:",
        reply_markup=reply_markup
    )

def main():
    """Fonction principale pour démarrer le bot"""
    # Création de l'application
    application = Application.builder().token(TOKEN).build()

    # Ajout des handlers
    application.add_handler(CommandHandler("start", start))

    # Démarrage du bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # Démarrage du serveur Flask dans un thread séparé
    from threading import Thread
    thread = Thread(target=lambda: app.run(host='0.0.0.0', port=5000))
    thread.start()
    
    # Démarrage du bot
    main() 