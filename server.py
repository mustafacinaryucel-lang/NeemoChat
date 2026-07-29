import os
from flask import Flask, render_template_string
from flask_socketio import SocketIO, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# Sunucu uyuşmazlıklarını önlemek için eventlet altyapısını zorunlu kılıyoruz
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kanka Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cloudflare.com"></script>
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
        // Sunucu adresini otomatik algılaması için boş bırakıyoruz
        var socket = io(); 
        var nickname = prompt("Kullanıcı adını gir kanka:");
        if(!nickname) nickname = "Misafir";

        socket.on('message', function(msg) {
            var p = document.createElement('p');
            p.innerHTML = msg;
            document.getElementById('chat').appendChild(p);
            var chatDiv = document.getElementById('chat');
            chatDiv.scrollTop = chatDiv.scrollHeight;
        });

        document.getElementById('sendButton').onclick = function() {
            var input = document.getElementById('myMessage');
            if(input.value.trim() !== "") {
                socket.send(nickname + ": " + input.value);
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
    # Render sunucusunun atayacağı portu otomatik yakalamasını sağlıyoruz
    port = int(os.environ.get("PORT", 55555))
    socketio.run(app, host='0.0.0.0', port=port)
