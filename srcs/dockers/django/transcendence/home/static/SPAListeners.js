function SPARedirect(event) {
	event.preventDefault();
	const section = this.getAttribute("data-section");
	if (section) {
		loadSection(section);
	}
}

let firstLoad = true;
async function loadSection(section, forceReload = false) {
	updatePageTitle(section.split("/")[section.split("/").length - 1]);
	if (section === "") {
		section = "home";
	}
	if (forceReload === false && window.location.pathname === `/${section}/`) {
		return;
	}
	if (window.location.pathname === "/chat/") {
		onChatSocketClose();
	} else if (window.location.pathname === "/game/waiting/") {
		if (socket) {
			socket.close();
			socket = null;
		}
	} else if (window.location.pathname.includes("game/single") || window.location.pathname.includes("game/multi")) {
		localSocketOperations("close");
	}
	if (socketGame) {
		await socketGame.close();
		socketGame = null;
	}
	if (gameTournament !== null) {
		await gameTournamentSocketOperations("close");
		await tournamentSocketOperations("close");
	}

	const response = await fetch("/" + section + "/", {
		method: "GET",
		headers: {
			"X-Requested-With": "XMLHttpRequest",
			"content-type": "text/html",
		},
	});

	if (!response.ok) {
		if (section !== "home") {
			loadSection("home");
			return;
		}
	}
	if (response.redirected) {
		const url = new URL(response.url);
		path = url.pathname;
		if (path[path.length - 1] === "/") {
			path = path.slice(0, -1);
		}
		if (path[0] === "/") {
			path = path.slice(1);
		}
		section = path;
	}
	const htmlFetch = await response.text();
	detachAllSPA();
	document.getElementById("content").innerHTML = htmlFetch;
	if (friendStatusSocket === null && inTimeout === false) {
		await initFriendStatusWebSocket();
	}
	await updateNav();
	if (!firstLoad) {
		window.history.pushState(
			{ html: document.documentElement.innerHTML, section: section },
			"",
			`/${section}/`
		);
	} else {
		firstLoad = false;
		window.history.replaceState(
			{ html: document.documentElement.innerHTML, section: section },
			"",
			`/${section}/`
		);
	}
	if (section === "friend") {
		updateFriendList();
	} else if (section === "chat") {
		if (firstConnect === false) {
			await onChatSocketOpen();
		}
	}
	attachAllSPA();
	if (section === "game/single") {
		localSocketOperations("open");
		loadTabS();
	} else if (section === "game/multi") {
		localSocketOperations("open");
		loadTabM();
	} else if (section === "game/multi4") {
		localSocketOperations("open");
		loadTabM4();
	} else if (section === "game/tournament") {
		loadTabT();
	} else if (window.location.pathname === "/game/waiting/") {
		setUpMatchmaking();
	} else if (section.includes("game/remote/?room")) {
		if (window.user && window.user.is_playing === true) {
			return;
		}
		gameSocketOperations("open");
	}
}

async function updateNav() {
	section = "nav";
	const response = await fetch("/navbar/", {
		method: "GET",
		headers: {
			"X-Requested-With": "XMLHttpRequest",
			"content-type": "application/html",
			isUpdateBySPA: "navbarUpdateSPA",
		},
	});

	if (!response.ok) {
		throw new Error(`Erreur lors du chargement de la section ${section}`);
	}
	const html = await response.text();
	document.getElementById("navbar").innerHTML = html;
}

submitted = false;
function SPASubmit(event) {
	event.preventDefault();
	const form = this.closest("form");
	if (form) {
		const formData = new FormData(form);
		const section = this.getAttribute("data-section");
		if (section) {
			fetch("/" + section + "/", {
				method: "POST",
				headers: {
					"X-Requested-With": "XMLHttpRequest",
					"X-CSRFToken": getCookie("csrftoken"),
					"context-type": "application/json",
				},
				body: formData,
			})
				.then((response) => response.json())
				.then((response) => {
					if (response.success) {
						submitted = true;
						showError("", "", true);
						redirectTo = response.goto;
						if (response.profileUpdate || response.friendRequest) {
							form.reset();
						} else if (redirectTo) {
							loadSection(redirectTo, true);
						} else {
							loadSection("home");
						}
					} else {
						form.reset();
						if (response.error) {
							showError(response.intitule, response.error);
						} else if (response.errors) {
							for (const [key, value] of Object.entries(response.errors)) {
								showError(key, value);
							}
						}
					}
				})
				.catch((error) => {
				});
		}
		}
}

async function closeWebSocket() {
	if (friendStatusSocket) friendStatusSocket.close();
	await ChatSocketOperations("close");
	await localSocketOperations("close");
	await tournamentSocketOperations("close");
	if (socket) socket.close();
	if (socketGame) {
		socketGame.close();
		socketGame = null;
	}
	if (gameTournament !== null) {
		await gameTournamentSocketOperations("close");
	}
	// set timeout of 5 seconds to avoid spamming the server
	if (inTimeout === false) {
		inTimeout = true;
		setTimeout(initFriendStatusWebSocket, 5000);
	}
}

async function SPALogout(event) {
	event.preventDefault();
	await fetch("/members/logout/", {
		method: "POST",
		headers: {
			"X-Requested-With": "XMLHttpRequest",
			"X-CSRFToken": getCookie("csrftoken"),
			"context-type": "application/json",
		},
	})
		.then((response) => response.json())
		.then(async (response) => {
			if (response.success) {
				loadSection("home", true);
				await closeWebSocket();
			}
		})
		.catch((error) => {
		});
}

function attachAllSPA() {
	document.querySelectorAll(".spa_redirect").forEach((element) => {
		if (!element.hasEventListener) {
			element.addEventListener("click", SPARedirect);
			element.hasEventListener = true;
		}
	});
	document.querySelectorAll(".spa_submit").forEach((element) => {
		if (!element.hasEventListener) {
			element.addEventListener("click", SPASubmit);
			element.hasEventListener = true;
		}
	});
	document.querySelectorAll(".spa_logout").forEach((element) => {
		if (!element.hasEventListener) {
			element.addEventListener("click", SPALogout);
			element.hasEventListener = true;
		}
	});
}

function detachAllSPA() {
	document.querySelectorAll(".spa_redirect").forEach((element) => {
		if (element.hasEventListener) {
			element.removeEventListener("click", SPARedirect);
			element.hasEventListener = false;
		}
	});
	document.querySelectorAll(".spa_submit").forEach((element) => {
		if (element.hasEventListener) {
			element.removeEventListener("submit", SPASubmit);
			element.hasEventListener = false;
		}
	});
	document.querySelectorAll(".spa_logout").forEach((element) => {
		if (element.hasEventListener) {
			element.removeEventListener("click", SPALogout);
			element.hasEventListener = false;
		}
	});
}

async function updateProfile() {
	const response = await fetch("/members/profile/", {
		method: "GET",
		headers: {
			"X-Requested-With": "XMLHttpRequest",
			"content-type": "application/html",
			partialUpdate: true,
		},
	});
	if (!response.ok) {
		throw new Error("Erreur lors du chargement de la section profile");
	}
	temp = document.createElement("div");
	temp.innerHTML = await response.text();
	document.getElementById("username").innerHTML =
		temp.querySelector("#username").innerHTML;
	document.getElementById("email").innerHTML =
		temp.querySelector("#email").innerHTML;
	document.getElementById("avatar").innerHTML =
		temp.querySelector("#avatar").innerHTML;
	history.replaceState(
		{ html: document.documentElement.innerHTML, section: "members/profile" },
		"",
		"/members/profile/"
	);
}

savedNameOfModal = "";
function addEventModal(nameOfModal) {
	document
		.getElementById(nameOfModal)
		.addEventListener("hidden.bs.modal", handlingModalClose);
	savedNameOfModal = nameOfModal;
}

function handlingModalClose() {
	if (submitted === true) {
		if (savedNameOfModal === "changeInformationsModal") updateProfile();
		if (
			savedNameOfModal === "addAFriend" ||
			savedNameOfModal === "removeAfriend" ||
			savedNameOfModal === "acceptAfriend"
		)
			updateFriendList();
		submitted = false;
	}
	document.body.style = "overflow-y: scroll; background-size: cover; height: 100vh; background-attachment: fixed;";
	document
		.getElementById(savedNameOfModal)
		.removeEventListener("hidden.bs.modal", handlingModalClose);
}
