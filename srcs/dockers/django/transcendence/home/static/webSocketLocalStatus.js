let localSocket = null;
async function localSocketOperations(action = null) {
	if (action === "open") {
		if (localSocket !== null) {
			localSocket.close();
		}
		var wsScheme = window.location.protocol == "https:" ? "wss" : "ws";
		localSocket = new WebSocket(
			wsScheme + "://" + window.location.host + "/ws/localStatus/"
		);
		localSocket.onopen = onlocalSocketOpen;
		localSocket.onmessage = onlocalMessageReceived;
		localSocket.onclose = onlocalSocketClose;
	} else if (action === "close") {
		if (localSocket) {
			localSocket.close();
			localSocket = null;
		}
	}
}

function onlocalSocketOpen() {
}

function onlocalMessageReceived(event) {
}

function onlocalSocketClose() {
}
