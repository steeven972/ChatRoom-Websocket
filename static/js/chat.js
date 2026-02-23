
var username = prompt("Enter your username:");
var client_id = username ? username : Math.random().toString(16).slice(2, 8);
document.getElementById("ws-id").textContent = client_id;
const ws = new WebSocket(`ws://127.0.0.1:8000/ws/${client_id}`);

ws.onmessage = (event) => {
    const li = document.createElement("li");
    li.textContent = `${new Date().toLocaleTimeString()} - ${event.data}`;
    document.getElementById("chat").appendChild(li);
};



function send() {
    const input = document.getElementById("input-msg");
    ws.send(input.value);
    input.value = "";
}
