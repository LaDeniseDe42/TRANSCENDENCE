function updateFriendList() {
    const friendList = document.getElementById("friend-section");
    const removeFriendList = document.getElementById("remove_friend_list");
    const acceptFriendList = document.getElementById("accept_friend_list");
    const acceptButton = document.getElementById("buttonAccept");
    if (!friendList || !removeFriendList || !acceptFriendList) {
        return;
    }
    fetch("/friend/update_friend/", {
        method: "GET",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "content-type": "application/html",
        },
    })
        .then(response => {
            if (!response.ok) {
                throw new Error("Erreur lors du chargement de la liste d'amis");
            }
            return response.text();
        })
        .then(html => {
            test = document.createElement("div");
            test.innerHTML = html;
            friendDetachAllSPA();
            friendList.innerHTML = test.querySelector("#friendList").innerHTML;
            removeFriendList.innerHTML = test.querySelector("#removeList").innerHTML;
            acceptFriendList.innerHTML = test.querySelector("#acceptList").innerHTML;
            acceptButton.innerHTML = test.querySelector("#buttonAccept").innerHTML;
            window.history.replaceState({ html: document.documentElement.innerHTML, section: "friend" }, "", "/friend/");
            friendAttachAllSPA();
        });
}
