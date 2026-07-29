import os
from flask import Flask, render_template_string
from flask_socketio import SocketIO, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kanka Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script>
    // Güvenli https ve wss bağlantı hatasını çözen kararlı WebSocket yapısı
    var socket = {
        on: function(event, callback) { this["on" + event] = callback; },
        send: function(msg) { ws.send('42["message",' + JSON.stringify(msg) + ']'); }
    };
    var proto = window.location.protocol === "https:" ? "wss://" : "ws://";
    var ws = new WebSocket(proto + window.location.host + "/socket.io/?EIO=4&transport=websocket");
    ws.onopen = function() { console.log("Bağlantı Başarılı!"); };
    ws.onmessage = function(e) {
        if (e.data.startsWith('42["message",')) {
            var raw = e.data.substring(13, e.data.length - 1);
            var msg = JSON.parse(raw);
            if (socket.onmessage) socket.onmessage(msg);
        } else if (e.data.startsWith('0{')) {
            ws.send('40');
        }
    };
    var io = function() { return socket; };
    </script>
    <style>
        body { font-family: Arial, sans-serif; background: #2f3136; color: white; margin: 0; padding: 20px; }
        #chat { height: 300px; border: 1px solid #202225; background: #36393f; overflow-y: scroll; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
        input { width: 70%; padding: 10px; border: none; border-radius: 3px; color: black; }
        button { width: 25%; padding: 10px; background: #5865f2; color: white; border: none; border-radius: 3px; cursor: pointer; }
    </style>
</head>
<body>
    <h2>Discord Klon Chat</h2>
    <div id="chat"></div>
    <input id="myMessage" type="text" placeholder="Mesajını yaz kanka...">
    <button id="sendButton">Gönder</button>

    <script>
        var client = io();
        var nickname = prompt("Kullanıcı adını gir kanka:");
        if(!nickname) nickname = "Misafir";

        client.on('message', function(msg) {
            var p = document.createElement('p');
            p.innerHTML = msg;
            document.getElementById('chat').appendChild(p);
            var chatDiv = document.getElementById('chat');
            chatDiv.scrollTop = chatDiv.scrollHeight;
        });

        document.getElementById('sendButton').onclick = function() {
            var input = document.getElementById('myMessage');
            if(input.value.trim() !== "") {
                client.send(nickname + ": " + input.value);
                input.value = '';
            }
        };

        document.getElementById('myMessage').addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                document.getElementById('sendButton').click();
            }
        });
    </script>
</body>
</html>
"""

from flask import make_response

@app.route('/')
def index():
    response = make_response(HTML_TEMPLATE)
    response.headers['Content-Type'] = 'text/html'
    return response

@socketio.on('message')
def handleMessage(msg):
    print('Gelen Mesaj: ' + msg)
    send(msg, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 55555))
    socketio.run(app, host='0.0.0.0', port=port)
