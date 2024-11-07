let chatSocket = null;
let tournamentMessageHistory = [];
let tournamentNotification = false;
async function ChatSocketOperations(action = null) {
	if (action === "open") {
		if (chatSocket !== null) {
			chatSocket.close();
		}
		var wsScheme = window.location.protocol == "https:" ? "wss" : "ws";
		chatSocket = new WebSocket(
			wsScheme + "://" + window.location.host + "/ws/chat/"
		);
		chatSocket.onopen = onChatSocketOpen;
		chatSocket.onmessage = onChatMessageReceived;
		chatSocket.onclose = onChatSocketClose;
	} else if (action === "close") {
		if (chatSocket) {
			chatSocket.close();
			chatSocket = null;
		}
	}
}

// Fonction permettant d'envoyer un message sur le webSocket
// action: action à envoyer
// message: message à envoyer
// channel: channel sur lequel effectuer l'action
async function sendAction(action = null, message = null, channel = null) {
	if (chatSocket === null) {
		return;
	}
	showError(null, null, true);
	try {
		await chatSocket.send(
			JSON.stringify({
				action: action,
				message: message,
				channel: channel,
			})
		);
	} catch (e) {
	}
}

// base functions for the chat
let firstConnect = true;
async function onChatSocketOpen(e) {
	if (chatSocket === null) {
		return;
	}
	if (window.location.pathname === "/chat/") {
		if (tournamentNotification === true) {
			document.getElementById("tournamentNotif").style.display = "inline";
		}
		document
		.getElementById("joinPublic")
		.addEventListener("click", joinPublicChat);
		document.getElementById("sendMessage").addEventListener("click", sendMessage);
		document
		.getElementById("selectChannel")
		.addEventListener("change", changeChannel);
		document
		.getElementById("chat-log")
		.addEventListener("mouseup", syncDivsByChat);
		document
		.getElementById("chat-log")
		.addEventListener("touchend", syncDivsByChat);
		document
		.getElementById("user-log")
		.addEventListener("mouseup", syncDivsByUser);
		document
		.getElementById("user-log")
		.addEventListener("touchend", syncDivsByUser);
		addEventListener("keydown", enterSend);
	}
	if (firstConnect === true) {
		firstConnect = false;
	} else {
		sendAction("recoverInformations", null, null);
	}
	await sendAction("getUsersOnline", null, null);
}

async function onChatMessageReceived(e) {
	if (chatSocket === null) {
		return;
	}
	const data = JSON.parse(e.data);
	if (data['channel'] === "TOURNAMENT") {
		tournamentMessageHistory.push(data);
		// return;
		tournamentNotification = true;
		if (window.location.pathname === "/chat/") {
			let channel = document.getElementById("selectChannel").value;
			if (channel === "TOURNAMENT") {
				tournamentNotification = false;
			}
			if (tournamentNotification === true) {
				document.getElementById("tournamentNotif").style.display = "inline";
			}
		}
	}
	if (window.location.pathname !== "/chat/") {
		return;
	}
	let action = data["action"];
	let message = data["message"];
	let channel = data["channel"];
	let success = data["success"];
	if (action === "join") {
		if (success === true) {
			// joinChat parse the channel name and add it to the selectChannel
			await joinChat(channel, data);
		} else {
			showError("Error", message);
		}
	} else if (action === "leave") {
		leaveChannel(data);
	} else if (action === "send") {
		if (success === false) {
			showError("Error", message);
		}
		// receiveMessage add the message to the chat-log after checking if the author is muted or not
		receiveMessage(message, channel, data);
	} else if (action === "getUsers") {
		// get the users in the channel and add them to the user-log
		usersDiv = document.getElementById("user-log");
		usersDiv.innerHTML = "";
		users = data["users"];
		for (let user of users) {
			usersDiv.innerHTML += user + "<br>";
		}
	} else if (action === "getUsersOnline") {
		// show the users online in the user table
		showUsersOnline(data);
	} else if (action === "mute" || action === "unmute") {
		sendAction("getUsersOnline", null, null);
	} else if (action === "notification") {
		if (data['type'] === "chat_message")
		{
			document.getElementById("user" + data['author'] + "Notification").style.display = "inline";
		}
	} else if (action === "clearNotification") {
		sendAction("getUsersOnline", null, null);
	} else if (action === "gameButtons") {
		id = data["author"];
		if (data["sub_action"] === "ReceivedInvitation") {
			notif = document.getElementById("user" + id + "InvitationToPlay");
			if (notif) {
				notif.style.display = "inline";
			}
			buttonInvite = document.getElementById("inviteToPlay" + id);
			buttonInvite.innerHTML = "Accept invitation";
			buttonInvite.onclick = () => acceptInvitation(id);
		} else if (data["sub_action"] === "InvitationCanceled") {
			notif = document.getElementById("user" + id + "InvitationToPlay");
			if (notif) {
				notif.style.display = "none";
			}
			buttonInvite = document.getElementById("inviteToPlay" + id);
			buttonInvite.innerHTML = `Invite to play`;
			buttonInvite.classList.remove("disabled");
			buttonInvite.onclick = () => inviteToPlay(id);
		} else if (data["sub_action"] === "InvitationAccepted") {
			notif = document.getElementById("user" + id + "InvitationToPlay");
			if (notif) {
				notif.style.display = "none";
			}
			buttonInvite = document.getElementById("inviteToPlay" + id);
			buttonInvite.innerHTML = "Invitation accepted";
			buttonInvite.classList.add("disabled");
			buttonInvite.onclick = null;
			invitedAlready = false;
			redirectToGame = data["gameRoom"];
			loadSection(redirectToGame);
		} else if (data["sub_action"] === "Error") {
			sendAction("getUsersOnline", null, null);
			showError("Error", data["message"]);
		} else if (data["sub_action"] === "InvitationDeclined") {
			sendAction("getUsersOnline", null, null);
			invitedAlready = false;
		}
	}
	history.replaceState({ html: document.documentElement.innerHTML, section: "chat" }, null, window.location.pathname);
}

async function onChatSocketClose(e) {
	if (window.location.pathname !== "/chat/") {
		return;
	}
	sendAction("declineInvitation", null, null);
	invitedAlready = false;
	document
		.getElementById("joinPublic")
		.removeEventListener("click", joinPublicChat);
	document
		.getElementById("sendMessage")
		.removeEventListener("click", sendMessage);
	document
		.getElementById("selectChannel")
		.removeEventListener("change", changeChannel);
	document
		.getElementById("chat-log")
		.removeEventListener("mouseup", syncDivsByChat);
	document
		.getElementById("chat-log")
		.removeEventListener("touchend", syncDivsByChat);
	document
		.getElementById("user-log")
		.removeEventListener("mouseup", syncDivsByUser);
	document
		.getElementById("user-log")
		.removeEventListener("touchend", syncDivsByUser);
	removeEventListener("keydown", enterSend);
	document.getElementById("selectChannel").innerHTML = "";
}

// list of functions need for onChatMessageReceived
async function joinChat(channel, data) {
	const channelDup = channel;
	const selectChannel = document.getElementById("selectChannel");
	if (channel.startsWith("PUBLIC_")) {
		channel = channel.substring(7);
		channel += " (public)";
	} else if (channel.startsWith("PRIVATE_")) {
		channel = data["user"];
		channel += " (private)";
	}
	// verify if the channel is already in the selectChannel
	for (let i = 0; i < selectChannel.length; i++) {
		if (selectChannel.options[i].value === channelDup) {
			return;
		}
	}
	selectChannel.append(new Option(channel, channelDup));
	if (selectChannel.length === 1) {
		changeChannel();
		selectChannel.append(new Option("tournament updates", "TOURNAMENT"));
	}
}

function receiveMessage(message, channel, data) {
	author = data["author"];
	// check if the author is muted in the user table
	if (author) {
		mutedStatus = document.getElementById("mutedStatusUser-" + author);
		if (mutedStatus) {
			mutedStatus = mutedStatus.getAttribute("data-section");
			if (mutedStatus === "muted") {
				return;
			}
		}
	}

	if (document.getElementById("selectChannel").value === channel) {
		detachAllSPA();
		divChat = document.getElementById("chat-log");
		divChat.innerHTML += message + "<br>";
		scrollDown();
		// check if the message contain 'has joined the chanel' or 'has left the channel'
		if (
			message.includes("has joined the channel") ||
			message.includes("has left the channel")
		) {
			sendAction("getUsers", null, channel);
		}
		if (channel.startsWith("PRIVATE_")) {
			sendAction("clearNotification", null, channel);
		}
		attachAllSPA();
	}
}

function showUsersOnline(data) {
	detachAllSPA();
	detachPrivateChat();
	users = data["users"];
	friends = data["friends"];
	userLines = document.getElementById("userLines");
	userLines.innerHTML = "";
	addWaitingNotification = {};
	for (let user of users) {
		// adding the user id and username to the userLines
		newLine =  `<tr>
						<th scope="row">${user["id"]}</th>
						<td><a class="spa_redirect" href="#members/profile/${user["username"]}" data-section="members/profile/${user["username"]}">${user["username"]}</a></td>`
		// check if the user is a friend and add the check mark
		if (user["is_friend"] === true) {
			newLine += `<td><i class="bi bi-check-lg">Yes</i></td>`;
		} else {
			newLine += `<td><i class="bi bi-x-lg">No</i></td>`;
		}
		// check if the user is online and add the status
		if (user["is_playing"] === true) {
			newLine += `<td><span class="status-playing">PLAYING</span></td>`;
		} else if (user["is_online"] === true) {
			newLine += `<td><span class="status-online">ONLINE</span></td>`;
		} else {
			newLine += `<td><span class="status-offline">OFFLINE</span></td>`;
		}
		// add the launch private chat button
		if (checkIfPrivateLaunched(user["id"]) === true) {
			newLine += `<td><a class="btn btn-primary" data-section="${user["id"]}">Already in chat <i class="bi bi-circle-fill text-danger" id="user${user["id"]}Notification" style="display: none;"></i></a></td>`;
		} else {
			newLine += `<td><a class="btn btn-primary launch-private-chat" data-section="${user["id"]}">Launch <i class="bi bi-circle-fill text-danger" id="user${user["id"]}Notification" style="display: none;"></i></a></td>`;
		}
		// check if the user is muted and add the muted status
		id = user['id'];
		if (user["muted"] === true) {
			newLine += `<td id="mutedStatusUser-${id}" data-section="muted" onclick="muteOrUnmute('${id}', 'unmute')"><i class="bi bi-chat-left-fill">Muted</i></td>`;
		} else {
			newLine += `<td id="mutedStatusUser-${id}" data-section="unmuted" onclick="muteOrUnmute('${id}', 'mute')"><i class="bi bi-chat-left-fill">Not Muted</i></td>`;
		}
		// add the button to invite the user to play a pong game
		if (user["is_playing"] === false && user["is_online"] === true) {
			if (user["invitedYou"] === true){ 
				newLine += `<td><a class="btn btn-primary" id="inviteToPlay${user['id']}" onclick="acceptInvitation(${user['id']})">Accept Invitation</a></td>`;
			} else if (user["youInvited"] === true) {
				// cancel invitation
				newLine += `<td><a class="btn btn-primary" id="inviteToPlay${user['id']}" onclick="cancelInvitation(${user['id']})">Cancel invitation</a></td>`;
			} else {
				newLine += `<td><a class="btn btn-primary" id="inviteToPlay${user['id']}" onclick="inviteToPlay(${user['id']})">Invite to play</a></td>`;
			}
		} else {
			newLine += `<td><a class="btn btn-primary disabled">Invite to play</a></td>`;
		}
		newLine += `</tr>`;
		userLines.innerHTML += newLine;
		newLine = "";
		if (user["waiting_notification"] === true) {
			selectChannel = document.getElementById("selectChannel");
			if (selectChannel.length !== 0 && selectChannel.value.startsWith("PRIVATE_")) {
				if (selectChannel.value.includes(user["id"])) {
					continue;
				}
			}
			addWaitingNotification[user["id"]] = true;
		}
	}
	if (addWaitingNotification.length !== 0) {
		for (let key in addWaitingNotification) {
			document.getElementById("user" + key + "Notification").style.display = "inline";
		}
	}
	attachPrivateChat();
	attachAllSPA();
}

function attachPrivateChat() {
	document
		.querySelectorAll(".launch-private-chat")
		.forEach((element) => {
			element.addEventListener("click", launchPrivateChat);
			element.hasEventListener = true;
		});
}

function detachPrivateChat() {
	document
		.querySelectorAll(".launch-private-chat")
		.forEach((element) => {
			if (element.hasEventListener) {
				element.removeEventListener("click", launchPrivateChat);
				element.hasEventListener = false;
			}
		});
}

function joinPublicChat() {
	if (chatSocket === null) {
		return;
	}
	const input = document.getElementById("publicChannelNameJoin");
	let channelName = input.value;
	if (channelName === "") {
		return;
	}
	input.value = "";
	channelName = "PUBLIC_" + channelName;
	sendAction("join", null, channelName);
}

function launchPrivateChat() {
	if (chatSocket === null) {
		return;
	}
	userID = this.getAttribute("data-section");
	// check if the user is muted
	mutedStatus = document.getElementById("mutedStatusUser-" + userID);
	if (mutedStatus) {
		mutedStatus = mutedStatus.getAttribute("data-section");
		if (mutedStatus === "muted") {
			showError("Error", "You can't chat with a muted user");
			return;
		}
	}
	channelName = "PRIVATE_" + userID;
	sendAction("join", null, channelName);
	sendAction("getUsersOnline", null, null);
}

function leaveChannel(data) {
	if (data["success"] === false) {
		showError("Error", data["message"]);
		return;
	}
	const channel = data["channel"];
	const selectChannel = document.getElementById("selectChannel");
	for (let i = 0; i < selectChannel.length; i++) {
		if (selectChannel.options[i].value === channel) {
			selectChannel.remove(i);
			break;
		}
	}
	if (channel.startsWith("PRIVATE_")) {
		sendAction("getUsersOnline", null, null);
	}
	if (selectChannel.length === 0) {
		clearChatLog();
		clearUserLog();
		sendAction("join", null, "PUBLIC_global");
		showError("Information", "You left all the channels, global channel joined");
	} else {
		changeChannel();
	}
}

function sendMessage() {
	if (chatSocket === null) {
		return;
	}
	const input = document.getElementById("messageToSend");
	let message = input.value;
	if (message === "") {
		return;
	}
	input.value = "";
	const channel = document.getElementById("selectChannel").value;
	if (channel === "TOURNAMENT") {
		showError("Error", "You can't send messages in the tournament channel");
		return;
	}
	sendAction("send", message, channel);
}

function changeChannel() {
	const channel = document.getElementById("selectChannel").value;
	divChat = document.getElementById("chat-log");
	divUser = document.getElementById("user-log");
	divChat.innerHTML = "";
	divUser.innerHTML = "";
	if (channel === "TOURNAMENT") {
		for (let message of tournamentMessageHistory) {
			divChat.innerHTML += message["message"] + "<br>";
		}
		tournamentNotification = false;
		document.getElementById("tournamentNotif").style.display = "none";
	} else {
		sendAction("getHistory", null, channel);
		sendAction("getUsers", null, channel);
		if (channel.startsWith("PRIVATE_")) {
			sendAction("clearNotification", null, channel);
		}
	}
	scrollDown();
}

function enterSend(e) {
	if (e.key === "Enter") {
		document.getElementById("sendMessage").click();
	}
}

function scrollDown() {
	const divChat = document.getElementById("chat-log");
	divChat.scrollTop = divChat.scrollHeight;
}

function syncDivsByChat() {
	const divChat = document.getElementById("chat-log");
	const divUser = document.getElementById("user-log");
	divUser.style.height = divChat.offsetHeight + "px";
	scrollDown();
}

function syncDivsByUser() {
	const divChat = document.getElementById("chat-log");
	const divUser = document.getElementById("user-log");
	divChat.style.height = divUser.offsetHeight + "px";
	scrollDown();
}

function updateChatUserList() {
	sendAction("getUsersOnline", null, null);
}

function muteOrUnmute(userId, action) {
	if (chatSocket === null) {
		return;
	}
	sendAction(action, null, userId);

}

// functions called by a onclick event
function sortTable(columnIndex) {
	const table = document.getElementById("userTable");
	const rows = Array.from(table.rows).slice(1); // Exclure l'en-tête
	let isAscending = table
		.querySelectorAll("th")
		[columnIndex].classList.contains("asc");

	rows.sort((rowA, rowB) => {
		const cellA = rowA.cells[columnIndex].innerText;
		const cellB = rowB.cells[columnIndex].innerText;

		if (!isNaN(cellA) && !isNaN(cellB)) {
			return isAscending ? cellA - cellB : cellB - cellA;
		} else {
			return isAscending
				? cellA.localeCompare(cellB)
				: cellB.localeCompare(cellA);
		}
	});

	rows.forEach((row) => table.tBodies[0].appendChild(row));

	// Gestion des classes pour les flèches
	table.querySelectorAll("th").forEach((th) => {
		th.classList.remove("asc", "desc");
		const icon = th.querySelector("i");
		if (icon) {
			icon.classList.remove(
				"fa-sort-up",
				"fa-sort-down",
				"bi-arrow-up",
				"bi-arrow-down",
				"bi-arrow-up-down"
			);
			icon.classList.add("fa-sort"); // ou "bi-arrow-up-down" si tu utilises Bootstrap Icons
		}
	});

	const currentIcon = table
		.querySelectorAll("th")
		[columnIndex].querySelector("i");
	if (currentIcon) {
		if (isAscending) {
			table.querySelectorAll("th")[columnIndex].classList.remove("asc");
			table.querySelectorAll("th")[columnIndex].classList.add("desc");
			currentIcon.classList.remove("fa-sort");
			currentIcon.classList.add("fa-sort-down"); // ou "bi-arrow-down" pour Bootstrap Icons
		} else {
			table.querySelectorAll("th")[columnIndex].classList.remove("desc");
			table.querySelectorAll("th")[columnIndex].classList.add("asc");
			currentIcon.classList.remove("fa-sort");
			currentIcon.classList.add("fa-sort-up"); // ou "bi-arrow-up" pour Bootstrap Icons
		}
	}
}

function clearChatLog() {
	document.getElementById("chat-log").innerHTML = "";
}

function leaveChannelonClick() {
	const channel = document.getElementById("selectChannel").value;
	if (channel === "TOURNAMENT") {
		showError("Error", "You can't leave the tournament channel");
		return;
	}
	sendAction("leave", null, channel);
}

// utils functions
function clearUserLog() {
	document.getElementById("user-log").innerHTML = "";
}


function checkIfPrivateLaunched(id) {
	document.getElementById("selectChannel")
	for(let i = 0; i < selectChannel.length; i++) {
		if (selectChannel.options[i].value.startsWith("PRIVATE_")) {
			if (selectChannel.options[i].value.includes(id)) {
				return true;
			}
		}
	}
	return false;
}

invitedAlready = false;
function inviteToPlay(id) {
	if (invitedAlready === true) {
		showError("Error", "You already invited someone to play");
		return;
	}
	invitedAlready = true;
	sendAction("inviteToPlay", null, id);
	buttonInvite = document.getElementById("inviteToPlay" + id);
	if (buttonInvite) {
		buttonInvite.innerHTML = "Invitation sent";
		buttonInvite.classList.add("disabled");
		buttonInvite.onclick = null;
		buttonInvite.innerHTML = "Cancel invitation";
		buttonInvite.classList.remove("disabled");
		buttonInvite.onclick = () => cancelInvitation(id);
		
	}
}

function cancelInvitation(id) {
	sendAction("cancelInvitation", null, id);
	buttonInvite = document.getElementById("inviteToPlay" + id);
	if (buttonInvite) {
		buttonInvite.innerHTML = `Invite to play`;
		buttonInvite.classList.remove("disabled");
		buttonInvite.onclick = () => inviteToPlay(id);
	}
	invitedAlready = false;
}

function acceptInvitation(id) {
	if (invitedAlready === true) {
		showError("Error", "You cant accept an invitation while you invited someone");
		return;
	}
	sendAction("acceptInvitation", null, id);
}

function filterUsers() {
	const usernameFilterTextBox = document.getElementById("usernameFilter")
	usernameFilter = null;
	if (usernameFilterTextBox) {
		usernameFilter = usernameFilterTextBox.value;
	}
	const statusFilterSelect = document.getElementById("statusFilter")
	statusFilter = null;
	if (statusFilterSelect) {
		statusFilter = statusFilterSelect.value;	
	}
	const friendFilterSelect = document.getElementById("friendFilter")
	friendFilter = null;
	if (friendFilterSelect) {
		friendFilter = friendFilterSelect.value;
	}
	mutedFilterSelect = document.getElementById("muteFilter")
	if (mutedFilterSelect) {
		mutedFilter = mutedFilterSelect.value;
	}
	const table = document.getElementById("userTable");
	rows = Array.from(table.rows).slice(1); // Exclure l'en-tête
	// default display all rows
	for (let row of rows) {
		row.style = "";
	}
	// filter by username
	if (usernameFilter) {
		for (let row of rows) {
			// getting content of the first cell of the row
			let cell = row.cells[1];
			// recover the username from the innerHTML of the a tag in the cell
			link = cell.querySelector("a");
			if (link) {
				cell = link.innerText;
			}
			if (!cell.includes(usernameFilter)) {
				row.style.display = "none";
			}
		}
	}
	// filter by status
	if (statusFilter) {
		if (statusFilter !== "all") {
			// uppercase statusFilter
			statusFilter = statusFilter.toUpperCase();
			for (let row of rows) {
				if (row.cells[3].innerText !== statusFilter) {
					row.style.display = "none";
				}
			}
		}
	}
	// filter by friend
	if (friendFilter) {
		if (friendFilter !== "all") {
			// uppercase friendFilter
			if (friendFilter === "friend") {
				friendFilter = "Yes";
			} else {
				friendFilter = "No";
			}
			// get the row of the table
			for (let row of rows) {
				// getting content of the first cell of the row
				let cell = row.cells[2];
				// recover the username from the innerHTML of the a tag in the cell
				icon = cell.querySelector("i");
				if (icon) {
					cell = icon.innerText;
				}
				if (cell !== friendFilter) {
					row.style.display = "none";
				}
			}
		}
	}
	if (mutedFilter) {
		if (mutedFilter !== "all") {
			// uppercase mutedFilter
			for (let row of rows) {
				if (row.cells[5].getAttribute("data-section") !== mutedFilter) {
					row.style.display = "none";
				}
			}
		}
	}
}