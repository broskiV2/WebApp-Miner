// Initialisation de Telegram WebApp
let tg = window.Telegram.WebApp;
tg.expand();

// URL de l'API backend sur Render
const API_URL = 'https://webapp-miner.onrender.com';

function updateBalance() {
    fetch(`${API_URL}/api/balance`)
        .then(response => response.json())
        .then(data => {
            document.querySelector('.balance').textContent = data.balance.toFixed(8);
            const progress = (data.balance / data.total_pull) * 100;
            document.getElementById('progressBar').style.width = `${progress}%`;
            document.getElementById('miningRate').textContent = `${data.rate.toFixed(8)}/day`;
            document.getElementById('totalMined').textContent = data.balance.toFixed(8);
        })
        .catch(error => {
            console.error('Erreur lors de la mise à jour du solde:', error);
            tg.showAlert('Erreur de connexion au serveur. Réessayez plus tard.');
        });
}

function startMining() {
    tg.showAlert('Mining started! Check back later for your rewards.');
}

// Mise à jour du solde toutes les 5 secondes
setInterval(updateBalance, 5000);
updateBalance(); 