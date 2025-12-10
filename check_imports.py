# check_imports.py
# Execute este arquivo para verificar o que está disponível

print("Verificando importações do LangChain...\n")

# Verifica versão
try:
    import langchain
    print(f"✅ LangChain versão: {langchain.__version__}")
except Exception as e:
    print(f"❌ Erro ao importar langchain: {e}")

# Verifica o que está disponível em langchain.agents
try:
    import langchain.agents as agents
    print(f"\n✅ Módulo langchain.agents importado")
    print(f"Conteúdo disponível:")
    available = [item for item in dir(agents) if not item.startswith('_')]
    for item in available[:20]:  # Mostra os primeiros 20
        print(f"  - {item}")
except Exception as e:
    print(f"❌ Erro: {e}")

# Testa initialize_agent
try:
    from langchain.agents import initialize_agent
    print(f"\n✅ initialize_agent disponível")
except Exception as e:
    print(f"❌ initialize_agent não disponível: {e}")

# Testa AgentType
try:
    from langchain.agents import AgentType
    print(f"✅ AgentType disponível")
except Exception as e:
    print(f"❌ AgentType não disponível: {e}")

# Testa create_react_agent
try:
    from langchain.agents import create_react_agent
    print(f"✅ create_react_agent disponível")
except Exception as e:
    print(f"❌ create_react_agent não disponível: {e}")

# Testa AgentExecutor
try:
    from langchain.agents import AgentExecutor
    print(f"✅ AgentExecutor disponível")
except Exception as e:
    print(f"❌ AgentExecutor não disponível: {e}")

print("\n" + "="*60)
print("Execute: pip install --upgrade langchain langchain-community")
print("="*60)