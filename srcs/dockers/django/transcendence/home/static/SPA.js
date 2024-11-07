document.addEventListener("DOMContentLoaded", () => {
	// Chargement de la Section :
	array = window.location.pathname.split("/").slice(1);
	if (array[array.length - 1] == "") {
		array.pop();
	}
	if (array.length == 0) {
		array.push("home");
	}
	if (gotoRoot && gotoRoot != null) {
		array = [];
		array.push(gotoRoot);
	}
	loadSection(array.join("/"), true);
	window.addEventListener("popstate", historyRecover);
});