

window.onload = () => {
    const username = document.getElementById("username").textContent;

    if (!username || username === "None") {
        window.location.href = "/register";
        return;
    }

    const ws = new WebSocket(`ws://${window.location.host}/ws`);

    ws.onopen = () => {
        console.log("WebSocket connecté !");
    };

    ws.onmessage = (event) => {
        const li = document.createElement("li");
        li.textContent = event.data;
        document.getElementById("chat").appendChild(li);
    };

    window.send = function () {
        const input = document.getElementById("input-msg");
        ws.send(input.value);
        input.value = "";
    };
};