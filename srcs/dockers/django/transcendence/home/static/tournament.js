let tournamentSocket = null;
let joinedTournament = false;
let tournamentSec = null;
let tournamentInfo = null;

async function tournamentSocketOperations(action = null) {
	if (action === "open") {
		if (tournamentSocket !== null) {
			tournamentSocket.close();
		}
		var wsScheme = window.location.protocol == "https:" ? "wss" : "ws";
		tournamentSocket = new WebSocket(
			wsScheme + "://" + window.location.host + "/ws/tournament/"
		);
		tournamentSocket.onopen = onTournamentSocketOpen;
		tournamentSocket.onmessage = onTournamentMessageReceived;
		tournamentSocket.onclose = onTournamentSocketClose;
        tournamentSec = document.getElementById("tournamentSection");
        tournamentInfo = document.getElementById("tInfo");
        if (tournamentSec){
            tournamentSec.style.display = "block";
            tournamentInfo.innerHTML = "Waiting for tournament ..."
        }
	} else if (action === "close") {
		if (tournamentSocket) {
			await tournamentSocket.close();
			tournamentSocket = null;
            if (tournamentSec){
                tournamentSec.style.display = "none";
            }
		}
	}
}

async function onTournamentSocketClose(e) {
}

async function onTournamentMessageReceived(e) {
    const data = JSON.parse(e.data);
    if (tournamentSec) {
        if (data["action"] === "joinTournament") {
            tournamentInfo.innerHTML = `
            <div class="row" id="tournamentStatus">
                Tournament found !
            </div>
            <div class="row">
                <div class="tree">
                    <ul>
                        <li>
                            <p>Tournoi</p>
                            <ul id="finals">
                                <li>
                                    <p>Final : need to be determined</p>
                                </li>
                                <div id="demiFinals">
                                <ul>
                                    <li>
                                        <p class="border text-center text-break">Game 1 : ${data["game1"][0]["tournamentName"]} VS ${data["game1"][1]["tournamentName"]}</p>
                                    </li>
                                    <li>
                                        <p class="border text-center text-break">Game 2 : ${data["game2"][0]["tournamentName"]} VS ${data["game2"][1]["tournamentName"]}</p>
                                    </li>
                                </ul>
                                </div>
                            </ul>
                        </li>
                    </ul>
                </div>
            </div>
            `
        } else if (data["action"] === "joinMatch") {
            tournamentStatus = document.getElementById("tournamentStatus");
            if (tournamentStatus) {
                tournamentStatus.innerHTML = `
                <div class="col-10">
                    <p>Match found !</p>
                    <p>
                        Time remaining to join : <span id="countdown"></span>
                    </p>
                </div>
                <div class="col-2">
                    <button class="btn btn-success" id="btnJoin" onclick='joinGame(${data["nbT"]}, "${data["game"]}")'>
                        join game
                    </button>
                </div>
                `
            }
        } else if (data["action"] === "countdown") {
            countdown = document.getElementById("countdown");
            if (data["seconds"] === 0) {
                tournamentStatus = document.getElementById("tournamentStatus");
                if (tournamentStatus) {
                    details = "Waiting informations from server...";
                    if (data["details"] !== "")
                        details = data["details"];
                    tournamentStatus.innerHTML = `Time is up ! ${details}`; 
                }
            } else if (countdown) {
                countdown.innerHTML = data["seconds"];
            }
        } else if (data["action"] === "startGame") {
            await loadSection(`game/tournament/game/?room=${data["room"]}`);
            await gameTournamentSocketOperations("open", data["room"]);
        } else if (data["action"] === "waitingNextMatch") {
            tournamentStatus = document.getElementById("tournamentStatus");
            if (tournamentStatus) {

                tournamentStatus.innerHTML = "Waiting other match to be finished..."; 
            }
            tournamentDemiFinals = document.getElementById("demiFinals");
            if (tournamentDemiFinals) {
                tournamentDemiFinals.innerHTML = ""; 
            }
        } else if (data["action"] === "tournamentEnded") {
            tournamentStatus = document.getElementById("tournamentStatus");
            if (tournamentStatus) {
                tournamentStatus.innerHTML = "Tournament is finished !"; 
            }
            first = data["first"];
            second = data["second"];
            third = data["third"];
            fourth = data["fourth"];
            tournamentFinals = document.getElementById("finals");
            if (tournamentFinals) {
                tournamentFinals.innerHTML = `
                <li>
                    <p>Classement final du tournois : </p>
                    <ul>
                        <li>
                            <p>1er : ${first} </p>
                        </li>
                        <li>
                            <p>2eme : ${second} </p>
                        </li>
                        <li>
                            <p>3eme : ${third} </p>
                        </li>
                        <li>
                            <p>4eme : ${fourth} </p>
                        </li>
                    </ul/
                </li>
                `
            }
        } else if (data["action"] === "tournamentUpdate"){
            tournamentFinals = document.getElementById("finals");
            if (tournamentFinals) {
                tournamentFinals.innerHTML = `
                <li>
                    <p>Final : ${data["final1"][0]["tournamentName"]} VS ${data["final1"][1]["tournamentName"]}</p>
                </li>
                <li>
                    <p>Little Final : ${data["final2"][0]["tournamentName"]} VS ${data["final2"][1]["tournamentName"]}</p>
                </li>
                `
            }

        } else if (data["action"] === "playerDisconnected") {
            tournamentStatus = document.getElementById("tournamentStatus");
            if (tournamentStatus) {
                tournamentStatus.innerHTML = `Player ${data["username"]} has disconnected.`;
            }
        } else if (data["action"] === "cancelTournament") {
            tournamentStatus = document.getElementById("tournamentStatus");
            if (tournamentStatus) {
                tournamentStatus.innerHTML = `Tournament cancelled, not enough players accepted games to launch the tournament.`;
            }
        } else if (data["action"] === "finalsAborted") {
            tournamentStatus = document.getElementById("tournamentStatus");
            if (tournamentStatus) {
                tournamentStatus.innerHTML = `Finals cancelled, not enough players accepted games to launch the tournament.`;
            }
        } else if (data["action"] === "cancelMatch") {
            const countdownElement = document.getElementById("countdown");
            if (countdownElement) {
                countdownElement.innerHTML = "";
            }
            tournamentStatus = document.getElementById("tournamentStatus");
            if (tournamentStatus) {
                tournamentStatus.innerHTML = `Match ${data["game"]} cancelled. Player ${data["username"]} has disconnected. The remaining player is declared the winner.`;
            }
        } else if (data["action"] === "waitingForTheResult") {
            tournamentStatus = document.getElementById("tournamentStatus");
            if (tournamentStatus) {

                tournamentStatus.innerHTML = "Waiting for the results.."; 
            }
        }
    }
}

async function joinGame(tournament=null, game=null) {
    if (tournament >= 0 && game) {
        tournamentSocket.send(JSON.stringify({
            "action": "joinGame",
            "nbT": tournament,
            "game": game
        }));
        buttonJoinGame = document.getElementById("btnJoin");
        if (buttonJoinGame) {
            buttonJoinGame.disabled = true;
            buttonJoinGame.innerHTML = "Waiting for other player";
        } 
    }
}

async function onTournamentSocketOpen(e) {
}

async function joinTournament() {
    // recup l'input value
    pseudoInput = document.getElementById("tournamentNickName")
    let pseudo = ""
    if (pseudoInput)
        pseudo = pseudoInput.value
    // envoie la requete
    await fetch("/game/tournament/", {
        method: "POST",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken"),
            "content-type": "application/json",
            "tournamentNick": pseudo,
        },
    })
        .then((response) => response.json())
        .then(data => {
            success = data["success"]
            if (success === true) {
                loadSection('home');
                tournamentSocketOperations("open");
            } else {
                showError("", "", true)
                // showError("Error in post", "the username you entered is invalid")
                showError("Information", data["error"])
            }
        }); 
}

async function exitTournament() {
    try {
        await tournamentSocketOperations("close");
    } catch (error) {
    }
    await loadSection("home");
}

let gameTournament = null;
async function gameTournamentSocketOperations(action = null, room = null) {
	if (action === "open") {
		if (gameTournament !== null) {
			gameTournament.close();
		}
		var wsScheme = window.location.protocol == "https:" ? "wss" : "ws";
		gameTournament = new WebSocket(
			wsScheme + "://" + window.location.host + "/ws/tournament_game/" + room + "/"
		);
		gameTournament.onopen = onGameTournamentOpen;
		gameTournament.onmessage = onGameTournamentMessageReceived;
		gameTournament.onclose = onGameTournamentClose;
        if (tournamentSec){
            tournamentSec.style.display = "none";
        }
	} else if (action === "close") {
		if (gameTournament) {
			await gameTournament.close();
			gameTournament = null;
            deactiveMove();
            if (tournamentSec){
                tournamentSec.style.display = "block";
            }
		}
	}
}

async function onGameTournamentOpen(e) {
}

async function onGameTournamentClose(e) {
}

var tPlayerPaddle = null;
var tgameInProgress = false;
let tgameEndHandled = false;

async function onGameTournamentMessageReceived(e) {
    const data = JSON.parse(e.data);
    if (data["action"] === 'assign_paddle') {
        tPlayerPaddle = data["paddle"];
    } else if (data["action"] === 'countdown') {
        tUpdateCountdown(data["seconds"]);
    } else if (data["action"] === 'game_start') {
        tstartGame(data["player1tournamentName"], data["player2tournamentName"]);
    } else if (data['type'] === 'game_state') {
        PADDLE_SPEED = data['paddle_speed'];
        tupdateGameState(data['game_state']);
    } else if (data["action"] === 'game_end' && !tgameEndHandled) {
        tgameInProgress = false;
        tgameEndHandled = true;
        if (data["winner"] === tPlayerPaddle)
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
                    text: 'Vous avez gagné ! Rejoignez vite la prochaine partie !',
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
                text: 'Vous avez perdu! Rejoignez vite la prochaine partie !',
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
        }, 100);
    }
}

function tstartGame(player1, player2) {
    // Mettre à jour les noms des joueurs
    document.getElementById('player1Name').innerText = player1;
    document.getElementById('player2Name').innerText = player2;
    // Réinitialiser le décompte
    document.getElementById('tcountdown').innerText = '';
    
    tgameInProgress = true;
    tgameEndHandled = false;
    initMove();
}
    


function tUpdateCountdown(seconds) {
    const countdownElement = document.getElementById('tcountdown');
    const aRetirer = document.getElementById('countdownd');
    countdownElement.innerText = seconds;
    if (seconds == 1) {
        aRetirer.innerText = '';
    }
}


function tupdateGameState(gameState) {
    if (!tgameInProgress) return;
    document.getElementById('player1Score').innerText = gameState.scores.player1;
    document.getElementById('player2Score').innerText = gameState.scores.player2;
    const canvas = document.getElementById('gameBoard');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    canvas.width = GAME_WIDTH;
    canvas.height = GAME_HEIGHT;

    ctx.beginPath();
    ctx.arc(gameState.ball_position.x, gameState.ball_position.y, gameState.ball_size, 0, Math.PI * 2);
    ctx.fillStyle = PINK;
    ctx.fill();
    ctx.closePath();

    ctx.fillStyle = PINK;
    ctx.fillRect(gameState.ball_size, gameState.paddle_positions.player1, gameState.paddle_width, gameState.paddle_height);
    ctx.fillRect(GAME_WIDTH - gameState.paddle_width - gameState.ball_size, gameState.paddle_positions.player2, gameState.paddle_width, gameState.paddle_height);
}


window.addEventListener('beforeunload', () => {
    if (gameTournament) {
        gameTournamentSocketOperations("close");
    }
});


let tanimationFrameId = null;
let tisMoving = false;

function initMove() {
    document.addEventListener('keydown', function(e) {
        if (!tgameInProgress) return;
        const key = e.key;
        let move = null;
        if (key === 'w') {
            move = "up";
        } else if (key === 's') {
            move = "down";
        } else {
            return;
        }
        if (!tisMoving && tPlayerPaddle) {
            tisMoving = true;
            animatePaddleMove(move);
        }
    });

    window.addEventListener('blur', function() {
        if (tisMoving) {
            tisMoving = false;
            if (tanimationFrameId) {
                cancelAnimationFrame(tanimationFrameId);
            }
        }
    });

    document.addEventListener('keyup', function(e) {
        const key = e.key;

        if (key === 'w' || key === 's') {
            targetY = 0;
            tisMoving = false;
            if (tanimationFrameId) {
                cancelAnimationFrame(tanimationFrameId);
            }
        }
    });

    function animatePaddleMove(move = null) {
        const step = () => {
            if (move !== null) {
                sendPaddleMove(move);
                tanimationFrameId = requestAnimationFrame(step);
            }
        };
        step();
    }

    function sendPaddleMove(move) {
        // Envoyer la nouvelle position de la raquette au serveur
        if (gameTournament && gameTournament.readyState === WebSocket.OPEN)
            gameTournament.send(JSON.stringify({
                    'action': 'paddle_move',
                    'player': tPlayerPaddle,
                    'move': move
                }
            ));
    }
}

function deactiveMove() {
    document.removeEventListener('keydown', function(e) {});
    document.removeEventListener('keyup', function(e) {});
    window.removeEventListener('blur', function() {});
}