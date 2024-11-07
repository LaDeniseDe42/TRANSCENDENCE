


// Initialisation de la connexion WebSocket pour le statut des amis
let friendStatusSocket = null;
let inTimeout = false;
async function initFriendStatusWebSocket() {
    await fetch('/members/check_login_status/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => {
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            throw new Error('Response is not JSON');
        }
    })
    .then(async data => {
        if (data.is_logged_in) {
            inTimeout = false;
            var wsScheme = window.location.protocol == "https:" ? "wss" : "ws";
            friendStatusSocket = new WebSocket(
                wsScheme + '://' + window.location.host + '/ws/status/'
            );
    
            friendStatusSocket.onopen = onFriendStatusSocketOpen;
            friendStatusSocket.onmessage = onFriendStatusMessageReceived;
            friendStatusSocket.onclose = onFriendStatusSocketClose;
            await ChatSocketOperations("open");
        }
        else
        {
            inTimeout = true;
            setTimeout(initFriendStatusWebSocket, 5000);
        }
    })
}


function onFriendStatusSocketOpen(e) {
}

// Traitement des messages reçus via WebSocket
async function onFriendStatusMessageReceived(e)
{
    const data = JSON.parse(e.data);
    const msg_rsvd = data.message;
    //si le message contient "is now online" ou "is now offline"
    if (msg_rsvd.includes('is now online') || msg_rsvd.includes('is now offline')
        || msg_rsvd.includes('a accepté votre demande d\'ami') || msg_rsvd.includes('Vous avez reçu une demande d\'ami de')
        || msg_rsvd.includes('vous a retiré de sa liste d\'amis') || msg_rsvd.includes('a changé de nom d\'utilisateur'))
    {
        // on met à jour l'UI
        updateFriendList();
        updateChatUserList();
    } else if (msg_rsvd.includes('DISCONNECTED'))
    {
        await closeWebSocket();
        loadSection('home');
    }
}

// Gestion de la fermeture de la connexion WebSocket
function onFriendStatusSocketClose(e) {  
}

// Envoi d'un message via WebSocket
function sendFriendStatusMessage(message) {
    friendStatusSocket.send(JSON.stringify({ 'message': message }));
}


