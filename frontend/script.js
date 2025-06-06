// ... (Toutes les parties map, getColor, fetchAndDisplayPredictions, geolocateBtn sont inchangées)

// --- LOGIQUE DE CHAT CONNECTÉE À L'API ---
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatDisplay = document.getElementById('chat-display');

// Fonction pour ajouter un message à l'écran
function addMessageToChat(message, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);
    // Pour gérer les sauts de ligne si l'IA en renvoie
    messageElement.innerHTML = message.replace(/\n/g, '<br>'); 
    chatDisplay.appendChild(messageElement);
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

// Gérer la soumission du formulaire de chat
chatForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const userMessage = chatInput.value.trim();

    if (userMessage) {
        // 1. Affiche le message de l'utilisateur
        addMessageToChat(userMessage, 'user');
        chatInput.value = '';

        // 2. Affiche un indicateur de "frappe" du bot
        addMessageToChat("...", 'bot-typing');

        try {
            // 3. Appelle notre propre backend pour obtenir une réponse de l'IA
            const response = await fetch('http://127.0.0.1:5000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage }),
            });

            // Supprime l'indicateur "..."
            document.querySelector('.bot-typing').remove();

            if (!response.ok) {
                throw new Error('La réponse du serveur n\'était pas OK');
            }

            const data = await response.json();
            // 4. Affiche la vraie réponse de l'IA
            addMessageToChat(data.reply, 'bot');

        } catch (error) {
            console.error("Erreur lors de la communication avec le chatbot:", error);
            addMessageToChat("Désolé, je n'arrive pas à me connecter à mon cerveau... 🧠 Réessayez plus tard.", 'bot');
        }
    }
});


// --- Lancement au chargement ---
fetchAndDisplayPredictions();