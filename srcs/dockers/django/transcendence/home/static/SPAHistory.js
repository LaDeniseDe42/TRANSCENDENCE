function historyRecover(event) {
	if (event.state && event.state.section) {
		detachAllSPA();
		document.documentElement.innerHTML = event.state.html;
		document.body.style.overflow = "auto";
		localSocketOperations("close");
		if (socketGame) {
			socketGame.close();
			socketGame = null;
		}
		if (socket) {
			socket.close();
			socket = null;
		}
		gameTournamentSocketOperations("close");
		tournamentSocketOperations("close");
		attachAllSPA();
		if (Swal.isVisible()) {
			Swal.close();
		}
	}
}
