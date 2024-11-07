
function filterHistory() {
    let gameModeSelect = document.getElementById('modeFilter');
    let gameMode = null;
    if (gameModeSelect !== null) {
        gameMode = gameModeSelect.value
    }
    let worlSelect = document.getElementById('worl');
    if (worlSelect !== null) {
        worl = worlSelect.value
    }
    const table = document.getElementById("historyTable");
    // exclude the header row
	rows = Array.from(table.rows).slice(1);
    for (let row of rows) {
		row.style = "";
	}
    if (gameMode !== null) {
        if (gameMode !== "All") {
            for (let row of rows) {
                let classList = row.classList;
                let mode = "mode_" + gameMode;
                if (classList.contains(mode) === false) {
                    row.style.display = "none";
                }
            }
        }
    }
    let username = document.getElementById('username').innerText;
    if (worl !== null) {
        if (worl !== "All") {
            for (let row of rows) {
                let classList = row.classList;
                if (worl === "Win") {
                    loserClass = "loser_" + username;
                    if (classList.contains(loserClass) === true) {
                        row.style.display = "none";
                    }
                } else if (worl === "Lose") {
                    winnerClass = "winner_" + username;
                    if (classList.contains(winnerClass) === true) {
                        row.style.display = "none";
                    }
                }
            }
        }
    }
    rowsForStats = [];
    for (let row of rows) {
        if (row.style.display !== "none") {
            rowsForStats.push(row);
        }
    }
    nbOfWins = 0;
    nbOfLoses = 0;
    pointsTaken = 0;
    pointsScored = 0;
    for (let row of rowsForStats) {
        let classList = row.classList;
        if (classList.contains("winner_" + username)) {
            nbOfWins++;
            pointsScored += parseInt(row.cells[2].innerText);
            pointsTaken += parseInt(row.cells[3].innerText);
        }
        if (classList.contains("loser_" + username)) {
            nbOfLoses++;
            pointsScored += parseInt(row.cells[3].innerText);
            pointsTaken += parseInt(row.cells[2].innerText);
        }
    }
    pieChart = document.getElementById("pieChart");
    if (pieChart !== null) {
        pieChart.style.setProperty("--win-percentage", nbOfWins);
        pieChart.style.setProperty("--lose-percentage", nbOfLoses);
    }
    statsNumber = document.getElementById("statsNumber");
    if (statsNumber !== null) {
        statsNumber.innerText = `${nbOfWins} WIN / ${nbOfLoses} LOSE`;
    }
    pointsTakenElement = document.getElementById("pointsTaken");
    pointsScoredElement = document.getElementById("pointsScored");
    if (pointsTakenElement !== null && pointsScoredElement !== null) {
        pointsTakenElement.innerText = pointsTaken;
        pointsScoredElement.innerText = pointsScored;
    }
}