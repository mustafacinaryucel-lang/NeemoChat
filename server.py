import os
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Mesajları sunucu hafızasında tutacak liste
messages_list = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>NeemoChat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #2f3136; color: white; margin: 0; padding: 20px; }
        #chat { height: 300px; border: 1px solid #202225; background: #36393f; overflow-y: scroll; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
        input { width: 70%; padding: 10px; border: none; border-radius: 3px; color: black; }
        button { width: 25%; padding: 10px; background: #5865f2; color: white; border: none; border-radius: 3px; cursor: pointer; }
        p { margin: 5px 0; padding: 20px; background: #40444b; border-radius: 5px; }
    </style>
</head>
<body>
    <h2>Discord Klon Chat</h2>
    <div id="chat"></div>
    <input id="myMessage" type="text" placeholder="Mesajını yaz kanka...">
    <button id="sendButton">Gönder</button>

    <script>
        var nickname = prompt("Kullanıcı adını gir kanka:");
        if(!nickname) nickname = "Misafir";

        // Mesaj gönderme fonksiyonu (Güvenli HTTP)
        function sendMessage() {
            var input = document.getElementById('myMessage');
            var msgText = input.value.trim();
            if(msgText !== "") {
                fetch('/send_message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: nickname + ": " + msgText })
                });
                input.value = '';
            }
        }

        document.getElementById('sendButton').onclick = sendMessage;
        document.getElementById('myMessage').addEventListener("keypress", function(event) {
            if (event.key === "Enter") sendMessage();
        });

        # Yeni mesajları her saniye sunucudan kontrol eden sistem
        setInterval(function() {
            fetch('/get_messages')
            .then(res => res.json())
            .then(data => {
                var chatDiv = document.getElementById('chat');
                chatDiv.innerHTML = '';
                data.forEach(msg => {
                    var p = document.createElement('p');
                    p.innerHTML = msg;
                    chatDiv.appendChild(p);
                });
            });
        }, 1000); // 1 saniyede bir ekranı günceller
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

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    if data and 'message' in data:
        messages_list.append(data['message'])
    return jsonify({"status": "ok"})

@app.route('/get_messages', methods=['GET'])
def get_messages():
    return jsonify(messages_list)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 55555))
    app.run(host='0.0.0.0', port=port)
