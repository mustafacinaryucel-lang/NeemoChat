import os
from flask import Flask, render_template_string, request, jsonify, make_response

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

messages_list = []
voice_peers = {} 

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>NeemoChat - Voice</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #2f3136; color: white; margin: 0; padding: 20px; }
        #chat { height: 250px; border: 1px solid #202225; background: #36393f; overflow-y: scroll; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
        .controls { display: flex; gap: 10px; margin-bottom: 10px; }
        input { flex: 1; padding: 10px; border: none; border-radius: 3px; color: black; font-size: 16px; }
        button { padding: 10px 20px; background: #5865f2; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 16px; }
        .voice-btn { background: #43b581; }
        .voice-btn.active { background: #f04747; }
        p { margin: 5px 0; padding: 8px; background: #40444b; border-radius: 5px; word-wrap: break-word; }
    </style>
</head>
<body>
    <h2>Discord Klon Chat & Voice</h2>
    
    <div class="controls">
        <button id="voiceButton" class="voice-btn">🎤 Sesli Odaya Katıl</button>
        <span id="voiceStatus" style="align-self: center; margin-left: 10px; color: #b9bbbe;">Ses: Bağlı Değil</span>
    </div>

    <div id="chat"></div>
    
    <div style="display: flex; gap: 10px;">
        <input id="myMessage" type="text" placeholder="Mesajını yaz kanka...">
        <button id="sendButton">Gönder</button>
    </div>

    <audio id="remoteAudio" autoplay></audio>

    <script>
        // HTTPS yönlendirmesini zorunlu kılıyoruz (Sesin çalışması için şart)
        if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
            location.replace(`https:${location.href.substring(location.protocol.length)}`);
        }

        var nickname = prompt("Kullanıcı adını gir kanka:");
        if(!nickname) nickname = "Misafir";

        let localStream;
        let peerConnection;
        let isVoiceConnected = false;

        const rtcConfig = {
            iceServers: [
                { urls: 'stun:://google.com' },
                { urls: 'stun:://google.com' }
            ]
        };

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

        setInterval(function() {
            fetch('/get_messages')
            .then(res => res.json())
            .then(data => {
                var chatDiv = document.getElementById('chat');
                if (chatDiv.childNodes.length !== data.length) {
                    chatDiv.innerHTML = '';
                    data.forEach(msg => {
                        var p = document.createElement('p');
                        p.innerHTML = msg;
                        chatDiv.appendChild(p);
                    });
                    chatDiv.scrollTop = chatDiv.scrollHeight;
                }
            });
        }, 1000);

        document.getElementById('voiceButton').onclick = async function() {
            const btn = document.getElementById('voiceButton');
            const status = document.getElementById('voiceStatus');

            if (!isVoiceConnected) {
                try {
                    // Mikrofon yakalama kodunu güncelledik
                    localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
                    peerConnection = new RTCPeerConnection(rtcConfig);
                    
                    localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));

                    peerConnection.ontrack = function(event) {
                        if (event.streams && event.streams[0]) {
                            document.getElementById('remoteAudio').srcObject = event.streams[0];
                        }
                    };

                    peerConnection.onicecandidate = function(event) {
                        if (event.candidate) {
                            fetch('/signal', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ user: nickname, candidate: event.candidate })
                            });
                        }
                    };

                    const offer = await peerConnection.createOffer();
                    await peerConnection.setLocalDescription(offer);

                    await fetch('/signal', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user: nickname, offer: offer })
                    });

                    btn.innerHTML = "❌ Odadan Ayrıl";
                    btn.classList.add('active');
                    status.innerHTML = "Ses: Odadasın (Mikrofon Açık)";
                    status.style.color = "#43b581";
                    isVoiceConnected = true;

                    startVoiceSignalingLoop();

                } catch (err) {
                    alert("Hata: Tarayıcı güvenli modda değil veya mikrofon donanımı meşgul!");
                    console.error(err);
                }
            } else {
                if(localStream) localStream.getTracks().forEach(track => track.stop());
                if(peerConnection) peerConnection.close();
                
                btn.innerHTML = "🎤 Sesli Odaya Katıl";
                btn.classList.remove('active');
                status.innerHTML = "Ses: Bağlı Değil";
                status.style.color = "#b9bbbe";
                isVoiceConnected = false;
            }
        };

        function startVoiceSignalingLoop() {
            let voiceInterval = setInterval(async function() {
                if (!isVoiceConnected) { clearInterval(voiceInterval); return; }

                const res = await fetch('/get_signals');
                const signals = await res.json();

                for (let user in signals) {
                    if (user !== nickname) {
                        if (signals[user].offer && !peerConnection.remoteDescription) {
                            await peerConnection.setRemoteDescription(new RTCSessionDescription(signals[user].offer));
                            const answer = await peerConnection.createAnswer();
                            await peerConnection.setLocalDescription(answer);
                            
                            fetch('/signal', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ user: nickname, answer: answer })
                            });
                        }
                        if (signals[user].answer && peerConnection.localDescription && !peerConnection.remoteDescription) {
                            await peerConnection.setRemoteDescription(new RTCSessionDescription(signals[user].answer));
                        }
                        if (signals[user].candidate) {
                            try {
                                await peerConnection.addIceCandidate(new RTCIceCandidate(signals[user].candidate));
                            } catch(e) {}
                        }
                    }
                }
            }, 1000);
        }
    </script>
</body>
</html>
"""

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

@app.route('/signal', methods=['POST'])
def signal():
    data = request.get_json()
    user = data.get('user')
    if user:
        if user not in voice_peers:
            voice_peers[user] = {}
        if 'offer' in data: voice_peers[user]['offer'] = data['offer']
        if 'answer' in data: voice_peers[user]['answer'] = data['answer']
        if 'candidate' in data: voice_peers[user]['candidate'] = data['candidate']
    return jsonify({"status": "ok"})

@app.route('/get_signals', methods=['GET'])
def get_signals():
    return jsonify(voice_peers)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 55555))
    app.run(host='0.0.0.0', port=port)
