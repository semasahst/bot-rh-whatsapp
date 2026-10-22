import os
import requests
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializa o Firebase (utiliza o ficheiro JSON de credenciais)
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

# Token de verificação do Webhook que definirá no painel da Meta
VERIFY_TOKEN = "rh_bot_token_seguro"

# Credenciais da API do WhatsApp (serão preenchidas quando obtiver os acessos)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "SEU_TOKEN_DA_META")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "SEU_PHONE_NUMBER_ID")

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
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        
        if "messages" in value:
            phone_number_id = value["metadata"]["phone_number_id"]
            message = value["messages"][0]
            from_phone = message["from"] # Número do colaborador
            message_body = message["text"]["body"].lower().strip()
            
            print(f"Mensagem recebida de {from_phone}: {message_body}")
            
            # 1. Busca a resposta correspondente no Firebase
            resposta_texto = buscar_resposta_faq(message_body)
            
            # 2. Envia a resposta de volta pelo WhatsApp
            enviar_mensagem_whatsapp(from_phone, resposta_texto)
            
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
        
    return jsonify({"status": "recebido"}), 200

def buscar_resposta_faq(pergunta_usuario):
    """Consulta a coleção faq_rh no Firestore para encontrar a resposta ideal."""
    docs = db.collection("faq_rh").stream()
    
    for doc in docs:
        dados = doc.to_dict()
        pergunta_cadastrada = dados.get("pergunta", "").lower()
        tags = [t.lower() for t in dados.get("tags", [])]
        
        # Verifica se a pergunta ou alguma tag corresponde ao texto enviado pelo funcionário
        if pergunta_cadastrada in pergunta_usuario or any(tag in pergunta_usuario for tag in tags):
            return dados.get("resposta")
            
    return "Desculpe, não encontrei uma resposta para essa dúvida no momento. O setor de RH será notificado."

def enviar_mensagem_whatsapp(destinatario, texto):
    """Envia a resposta de volta ao colaborador via WhatsApp Cloud API."""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": destinatario,
        "type": "text",
        "text": {"body": texto},
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
