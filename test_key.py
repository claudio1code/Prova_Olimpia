# test_key.py
import os
import google.generativeai as genai

key = os.environ.get("GEMINI_API_KEY")

print(f"🔑 Verificando chave: {key[:10]}...{key[-4:] if key else 'Nenhuma'}")

if not key:
    print("❌ Erro: Nenhuma chave detectada.")
    exit()

try:
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Responda apenas: OK, funcionou.")
    print(f"✅ SUCESSO! O Google respondeu: {response.text}")
except Exception as e:
    print(f"❌ FALHA: A chave foi rejeitada.\nErro detalhado: {e}")