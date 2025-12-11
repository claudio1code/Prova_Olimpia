import os
import re
import sys

from src.config import Colors
from src.utils import print_styled
from src.workflow import app

if __name__ == "__main__":
    # Limpa o terminal
    os.system("cls" if os.name == "nt" else "clear")

    print(f"{Colors.HEADER}{'=' * 60}")
    print(" 📊 AGENTE DE PESQUISA DE EMPRESAS")
    print(f"{'=' * 60}{Colors.ENDC}")

    try:
        # Pega o input via argumento ou prompt
        if len(sys.argv) > 1:
            target = " ".join(sys.argv[1:])
        else:
            target = input(f"\n👉 {Colors.BOLD}Empresa: {Colors.ENDC}").strip()

        # Limpa caracteres estranhos do input
        target = re.sub(r"\[\d+;?\d*[A-Z]", "", target).replace("^", "").strip()
        if not target:
            sys.exit()

        print(f"\n🚀 {Colors.BOLD}START: {target.upper()}{Colors.ENDC}")
        print("-" * 60)

        # Executa o Grafo
        res = app.invoke({"company_name": target})

        # Exibe o Resultado Final Formatado
        print("\n" + f"{Colors.GREEN}{'=' * 60}{Colors.ENDC}")
        print_styled(res["final_report"])
        print(f"{Colors.GREEN}{'=' * 60}{Colors.ENDC}" + "\n")

    except KeyboardInterrupt:
        print(f"\n{Colors.FAIL}Fim.{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Erro: {e}{Colors.ENDC}")
