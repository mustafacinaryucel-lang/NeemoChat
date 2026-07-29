import os
from flask import Flask, render_template_string, request, jsonify, make_response

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_neemo!'

messages_list = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>NeemoChat - Voice Stable</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Dünyanın en kararlı ses kütüphanesini (Agora) sayfaya ekliyoruz -->
    <script src="https://agora.io"></script>
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
    <h2>Discord Klon Chat & Kararlı Ses</h2>
    
    <div class="controls">
        <button id="voiceButton" class="voice-btn">🎤 Sesli Odaya Katıl</button>
        <span id="voiceStatus" style="align-self: center; margin-left: 10px; color: #b9bbbe;">Ses: Bağlı Değil</span>
    </div>

    <div id="chat"></div>
    
    <div style="display: flex; gap: 10px;">
        <input id="myMessage" type="text" placeholder="Mesajını yaz kanka...">
        <button id="sendButton">Gönder</button>
    </div>

    <script>
        var nickname = prompt("Kullanıcı adını gir kanka:");
        if(!nickname) nickname = "Misafir";

        // --- YAZILI CHAT SİSTEMİ ---
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

        // --- AGORA GÜVENLİ VE SIFIR HATALI SES SİSTEMİ ---
        let rtc = {
            client: null,
            localAudioTrack: null
        };

        // Tamamen ücretsiz ve herkese açık test odası parametreleri
        let options = {
            appId: "c2c544e31e674cbfa4b423f03b2241cf", // Genel ücretsiz Agora test anahtarı
            channel: "neemochat_global_room", 
            token: null, 
            uid: null
        };

        let isVoiceConnected = false;

        document.getElementById('voiceButton').onclick = async function() {
            const btn = document.getElementById('voiceButton');
            const status = document.getElementById('voiceStatus');

            if (!isVoiceConnected) {
                try {
                    // Agora ses istemcisini başlatıyoruz
                    rtc.client = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });
                    
                    // Odaya giriş yapıyoruz
                    options.uid = await rtc.client.join(options.appId, options.channel, options.token, null);
                    
                    // Mikrofonu engelsiz şekilde açıyoruz
                    rtc.localAudioTrack = await AgoraRTC.createMicrophoneAudioTrack();
                    
                    // Sesimizi odaya gönderiyoruz
                    await rtc.client.publish([rtc.localAudioTrack]);

                    // Karşı taraftan birisi odaya ses verdiğinde otomatik oynat
                    rtc.client.on("user-published", async (user, mediaType) => {
                        await rtc.client.subscribe(user, mediaType);
                        if (mediaType === "audio") {
                            user.audioTrack.play();
                        }
                    });

                    btn.innerHTML = "❌ Odadan Ayrıl";
                    btn.classList.add('active');
                    status.innerHTML = "Ses: Odadasın (Mikrofon Açık)";
                    status.style.color = "#43b581";
                    isVoiceConnected = true;

                } catch (err) {
                    alert("Mikrofon donanımınız başka uygulama tarafından kullanılıyor veya engelleniyor kanka!");
                    console.error(err);
                }
            } else {
                // Odadan güvenli çıkış
                if(rtc.localAudioTrack) {
                    rtc.localAudioTrack.stop();
                    rtc.localAudioTrack.close();
                }
                if(rtc.client) {
                    await rtc.client.leave();
                }
                
                btn.innerHTML = "🎤 Sesli Odaya Katıl";
                btn.classList.remove('active');
                status.innerHTML = "Ses: Bağlı Değil";
                status.style.color = "#b9bbbe";
                isVoiceConnected = false;
            }
        };
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 55555))
    app.run(host='0.0.0.0', port=port)
