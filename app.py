import os
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializa o Firebase
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

# Token de verificação que você definirá no painel da Meta
VERIFY_TOKEN = "rh_bot_token_seguro"

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Validação inicial exigida pela Meta para conectar o Webhook."""
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if token == VERIFY_TOKEN:
        return challenge, 200
    return "Token de verificação inválido", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    """Recebe as mensagens enviadas pelos colaboradores no WhatsApp."""
    data = request.json
    
    try:
        # Extrai a mensagem recebida da estrutura JSON da Meta
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        
        if "messages" in value:
            phone_number_id = value["metadata"]["phone_number_id"]
            message = value["messages"][0]
            from_phone = message["from"] # Número do colaborador
            message_body = message["text"]["body"].lower()
            
            print(f"Mensagem recebida de {from_phone}: {message_body}")
            
            # Aqui faremos a busca no Firebase nas próximas etapas
            
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
        
    return jsonify({"status": "recebido"}), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)