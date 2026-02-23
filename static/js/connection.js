/*var form = document.getElementById("connection-form");


form.addEventListener("Submit", (event)=>{
    event.preventDefault();
    var username = document.getElementById("username").value;
    var password = document.getElementById("password").value;
    var client_id = username ? username : Math.random().toString(16).slice(2, 8);
    document.getElementById("ws-id").textContent = client_id;
    const ws = new WebSocket(`ws://localhost:8000/ws/${client_id}?password=${password}`);
})*/