var socket = null
function setUpMatchmaking() {
    var wsScheme = window.location.protocol == "https:" ? "wss" : "ws";
    socket = new WebSocket(wsScheme + '://' + window.location.host + '/ws/matchmaking/');
    socket.onopen = function(e) {
    };

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'match_found') {
            const player1 = data.player1;
            const player2 = data.player2;
            const roomId = `REMOTE_${player1}VS${player2}`;
            // Envoyer le room_id aux deux joueurs
            socket.send(JSON.stringify({ type: 'room_id', room_id: roomId }));
            document.getElementById("waitingBox").innerHTML = "Inactive matchmaking, reload for relaunch it"
            history.replaceState({ html: document.documentElement.innerHTML, section: "/game/waiting/" + roomId }, "", "/game/waiting/");
            // Rediriger vers la salle de jeu
            loadSection(`game/remote/?room=${roomId}`);
        }
    };

    socket.onclose = function(e) {
        socket = null;
    };

    socket.onerror = function(e) {
    };
    // detecte si l'utilisateur utilise les fleches de l'historique
    window.onpopstate = function(e) {
        if (socket) {
            socket.send(JSON.stringify({ type: 'leave_queue' }));
            socket.close();
        }
    };
}

