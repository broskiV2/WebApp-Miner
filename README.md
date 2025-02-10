# WeMine - Bot Telegram USDT Miner

Un bot Telegram avec une webapp intégrée simulant un mineur USDT.

## Configuration requise

- Python 3.8+
- Un token de bot Telegram (à obtenir via [@BotFather](https://t.me/botfather))
- Un serveur pour héberger la webapp (ou utiliser ngrok pour le développement)

## Installation

1. Clonez ce dépôt :
```bash
git clone https://github.com/votre-username/wemine-bot.git
cd wemine-bot
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Créez un fichier `.env` à la racine du projet avec les variables suivantes :
```
TELEGRAM_TOKEN=votre_token_telegram
WEBAPP_URL=https://votre-domaine.com
```

## Démarrage

1. Lancez le bot :
```bash
python main.py
```

2. Ouvrez Telegram et cherchez votre bot
3. Envoyez la commande `/start` pour commencer

## Fonctionnalités

- Interface utilisateur moderne et réactive
- Simulation de minage USDT
- Mise à jour en temps réel des soldes
- Intégration complète avec Telegram WebApp

## Développement local

Pour tester localement avec ngrok :

1. Installez ngrok
2. Lancez ngrok :
```bash
ngrok http 5000
```
3. Copiez l'URL HTTPS générée par ngrok dans votre fichier `.env` comme WEBAPP_URL

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request. 