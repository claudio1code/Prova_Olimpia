import os
import sys
import importlib.util

print("="*60)
print("🔎 DIAGNÓSTICO DO AMBIENTE")
print("="*60 + "\n")

# 1. Verifica Chaves de API
print("1. Verificando Variáveis de Ambiente...")
gemini_key = os.environ.get("GEMINI_API_KEY")
if gemini_key:
    print(f"   ✅ GEMINI_API_KEY encontrada: {gemini_key[:5]}...{gemini_key[-4:]}")
else:
    print("   ❌ GEMINI_API_KEY NÃO encontrada!")
    print("      -> Execute: export GEMINI_API_KEY='sua_chave_aqui'")

print("-" * 30)

# 2. Verifica Instalação de Bibliotecas Críticas
packages = [
    ("langchain", "LangChain"),
    ("langgraph", "LangGraph"),
    ("yfinance", "yFinance"),
    ("langchain_google_genai", "Google GenAI"),
    ("duckduckgo_search", "DuckDuckGo (Pacote Novo)"),
]

print("2. Verificando Bibliotecas Instaladas...")
for package_name, display_name in packages:
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        print(f"   ❌ {display_name}: NÃO encontrado ({package_name})")
    else:
        print(f"   ✅ {display_name}: Instalado")

# Verificação Específica do Conflito DuckDuckGo
print("-" * 30)
print("3. Verificando Compatibilidade do DuckDuckGo...")
try:
    from duckduckgo_search import DDGS
    print("   ✅ Importação 'from duckduckgo_search import DDGS' funcionou (Versão Nova).")
except ImportError:
    print("   ⚠️ Importação nova falhou.")

try:
    import ddgs
    print("   ✅ Importação 'import ddgs' funcionou (Versão Antiga).")
except ImportError:
    print("   ℹ️ Importação 'import ddgs' falhou (Isso quebra o wrapper padrão do LangChain).")

print("-" * 30)

# 4. Teste de Conexão Rápido (Se possível)
if gemini_key:
    print("4. Testando Conexão com Gemini...")
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_key)
        res = llm.invoke("Teste rápido. Responda 'OK' se estiver me ouvindo.")
        print(f"   ✅ Gemini Respondeu: {res.content}")
    except Exception as e:
        print(f"   ❌ Erro ao conectar com Gemini: {e}")
else:
    print("4. Pular teste de conexão (sem chave).")

print("\n" + "="*60)
print("CONCLUSÃO")
if gemini_key and importlib.util.find_spec("duckduckgo_search"):
    print("✅ Seu ambiente parece pronto para usar o 'main.py' COM A CORREÇÃO MANUAL.")
    print("   (O wrapper padrão do LangChain pode falhar porque ele busca 'ddgs', mas você tem a versão nova).")
    print("   -> USE O CÓDIGO 'main.py' QUE TE PASSEI NO ÚLTIMO PASSO (ele corrige isso).")
else:
    print("❌ Corrija os erros acima antes de tentar rodar o agente.")