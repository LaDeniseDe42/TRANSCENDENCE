
let gameEndHandled = false;
var socketGame = null;
var playerPaddle = null;
var gameInProgress = false;
let isPaused = false;

const GAME_WIDTH = 600;
const GAME_HEIGHT = 400;
const ORANGE = '#FFA500';
const PINK = '#FF69B4';
const GREEN = '#00FF00';
const GREEN2 = '#0E942B';
const RED = '#FF0000';
const BLUE = '#0000FF';
const BLACK = '#000000';
const WHITE = '#FFFFFF';
let PADDLE_SPEED = 0;


async function gameSocketOperations(action = null) {
	if (action === "open") {
		if (socketGame !== null) {
			socketGame.close();
		}
        const urlParams = new URLSearchParams(window.location.search);
        const roomId = urlParams.get('room');
		var wsScheme = window.location.protocol == "https:" ? "wss" : "ws";
		socketGame = new WebSocket(
			wsScheme + "://" + window.location.host + "/ws/pong/" + roomId
		);
		socketGame.onopen = onsocketGameOpen;
		socketGame.onmessage = onsocketGameMessageReceived;
		socketGame.onclose = onsocketGameClose;
        if (tournamentSec){
            tournamentSec.style.display = "none";
        }
	} else if (action === "close") {
		if (socketGame) {
			await socketGame.close();
			socketGame = null;
            deactiveGameMove();
            if (tournamentSec){
                tournamentSec.style.display = "block";
            }
		}
	}
}

function onsocketGameOpen(e) {
}

function onsocketGameMessageReceived(e) {
    const data = JSON.parse(e.data);
    if (data["action"] === 'assign_paddle') {
        playerPaddle = data["paddle"];
    } else if (data["action"] === 'countdown') {
        updateCountdown(data["seconds"]);
    } else if (data["action"] === 'game_start') {
        startGame(data["player1tournamentName"], data["player2tournamentName"]);
    } else if (data['type'] === 'game_state') {
        PADDLE_SPEED = data['paddle_speed'];
        updateGameState(data['game_state']);
    } else if (data["action"] === 'game_end' && !gameEndHandled) {
        gameInProgress = false;
        gameEndHandled = true;
        if (data["winner"] === playerPaddle)
        {
            if (data["why"] === 'couard' || data["why"] === 'disconnected') {
                Swal.fire({
                    title: 'Your opponent has left the game.',
                    text: 'Vous avez gagné !',
                    icon: 'question',
                    imageUrl: '/static/images/coward.gif',
                    background: "rgba(255, 255, 255, 1)",
                    confirmButtonText: 'Return to home',
                    position: 'center',
                    });
            }
            else
                Swal.fire({
                    title: 'Félicitations !',
                    text: 'Vous avez gagné !',
                    icon: 'success',
                    imageUrl: '/static/images/won.gif',
                    background: "rgba(255, 255, 255, 1)",
                    confirmButtonText: 'Return to home',
                    position: 'center',
                    });
        }
        else
        {
            Swal.fire({
                title: 'ECHEC',
                text: 'Vous avez perdu!',
                icon: 'warning',
                imageUrl: '/static/images/dead.gif',
                background: "rgba(255, 255, 255, 1)",
                confirmButtonText: 'Return to home',
                position: 'center',
                });
        }
        gameTournamentSocketOperations("close");
        setTimeout(() => {
            loadSection('home');
        }, 100); // Délai de 100ms pour s'assurer que l'alerte est fermée
    }
}

function onsocketGameClose(e) {
    gameInProgress = false;
}

function moveGamePaddle(e) {
    if (!gameInProgress) {
        return;
    }
    const key = e.key;
    let move = null;
    if (key === 'w')
        move = 'up';
    else if (key === 's')
        move = 'down';
    else
        return;
    if (!isMoving && playerPaddle) {
        isMoving = true;
        animateGamePaddleMove(move);
    }
}

function stopGamePadle(e) {
    const key = e.key;
    if (key === 'w' || key === 's') {
        isMoving = false;
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
        }
    }
}

function animateGamePaddleMove(move = null) {
    const step = () => {
        if (isMoving) {
            sendGamePaddleMove(move);
            animationFrameId = requestAnimationFrame(step);
        }
    };
    step();
}

function sendGamePaddleMove(move) {
    if (socketGame && socketGame.readyState === WebSocket.OPEN) {
        socketGame.send(JSON.stringify({
            'action': 'paddle_move',
            'player': playerPaddle,
            'move': move
        }));
    }
}

function initGameMove() {
    document.addEventListener("keydown", moveGamePaddle);
    document.addEventListener("keyup", stopGamePadle);
    document.addEventListener("blur", cancelIfBlur);
}

function cancelIfBlur() {
    if (isMoving) {
        isMoving = false;
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
        }
    }
}

function deactiveGameMove() {
    document.removeEventListener("keydown", moveGamePaddle);
    document.removeEventListener("keyup", stopGamePadle);
    document.removeEventListener("blur", cancelIfBlur);
}

function updateCountdown(seconds) {
    const countdownElement = document.getElementById('countdown');
    const aRetirer = document.getElementById('countdownd');
    countdownElement.innerText = seconds;
    if (seconds == 1) {
        aRetirer.innerText = '';
    }
}

function startGame(player1, player2) {
    // Mettre à jour les noms des joueurs
    document.getElementById('player1Name').innerText = player1;
    document.getElementById('player2Name').innerText = player2;
    // Réinitialiser le décompte
    document.getElementById('countdown').innerText = '';
    
    gameInProgress = true;
    gameEndHandled = false;
    initGameMove();
}

let animationFrameId = null;
let isMoving = false;

function updateGameState(gameState) {
    if (!gameInProgress) return;
    document.getElementById('player1Score').innerText = gameState.scores.player1;
    document.getElementById('player2Score').innerText = gameState.scores.player2;
    const canvas = document.getElementById('gameBoard');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    canvas.width = GAME_WIDTH;
    canvas.height = GAME_HEIGHT;

    ctx.beginPath();
    ctx.arc(gameState.ball_position.x, gameState.ball_position.y, gameState.ball_size, 0, Math.PI * 2);
    ctx.fillStyle = GREEN;
    ctx.fill();
    ctx.closePath();

    ctx.fillStyle = GREEN2;
    ctx.fillRect(gameState.ball_size, gameState.paddle_positions.player1, gameState.paddle_width, gameState.paddle_height);
    ctx.fillRect(GAME_WIDTH - gameState.paddle_width - gameState.ball_size, gameState.paddle_positions.player2, gameState.paddle_width, gameState.paddle_height);
}



