# listar_modelos.py
import os
import google.generativeai as genai

# Configura a chave
key = os.environ.get("GEMINI_API_KEY")
if not key:
    print("❌ Defina a GEMINI_API_KEY")
    exit()

genai.configure(api_key=key)

print(f"🔍 Consultando modelos disponíveis para a chave final ...{key[-4:]}")
print("-" * 50)

try:
    # Lista tudo que a API devolve
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Disponível: {m.name}")
except Exception as e:
    print(f"❌ Erro ao listar: {e}")