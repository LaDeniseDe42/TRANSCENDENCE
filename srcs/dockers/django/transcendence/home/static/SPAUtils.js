function getCookie(name) {
	let cookieValue = null;
	if (document.cookie && document.cookie !== "") {
		const cookies = document.cookie.split(";");
		for (let i = 0; i < cookies.length; i++) {
			const cookie = cookies[i].trim();
			if (cookie.substring(0, name.length + 1) === name + "=") {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}

function showError(intitule = null, message = null, clear = false) {
	if (intitule === null) {
		intitule = "Error";
	}
	if (message === null) {
		message = "An error occured";
	}
	errorSection = document.getElementById("errorMessages");
	if (errorSection === null) {
		return;
	}
	if (clear) {
		errorSection.innerHTML = "";
		errorSection.style.display = "none";
	} else {
		errorSection.style.display = "block";
		errorSection.innerHTML += `<h5>${intitule}</h5><p>${message}</p>`;
	}
}

function updatePageTitle(section) {
    document.title = `${section} - Transcendence`;
}


function friendAttachAllSPA() {
	document.querySelectorAll(".loadMe").forEach((element) => {
		if (!element.hasEventListener) {
			element.addEventListener("click", SPARedirect);
			element.hasEventListener = true;
		}
	});
}

function friendDetachAllSPA() {
	document.querySelectorAll(".loadMe").forEach((element) => {
		if (element.hasEventListener) {
			element.removeEventListener("click", SPARedirect);
			element.hasEventListener = false;
		}
	});
}
