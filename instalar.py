"""Instala a skill gerenciar-modelo no Claude Code, pedindo autorização a cada passo.

Uso:
  python instalar.py                      instala (pergunta tudo antes de gravar)
  python instalar.py --modo performance   troca só o modo (economia | performance)
  python instalar.py --principal sonnet   troca o modelo da conversa principal (opus | sonnet | fable)
  python instalar.py --desinstalar        remove tudo o que o instalador gravou
"""
import json
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CLAUDE = Path.home() / ".claude"
CONTA = Path.home() / ".claude.json"
MODOS = ("economia", "performance")
PLANOS = ("Pro", "Max", "Ultra", "Team", "Enterprise", "API")
INICIO = "<!-- gerenciar-modelo:inicio -->"
FIM = "<!-- gerenciar-modelo:fim -->"
BLOCO = (
    f"{INICIO}\n"
    "# Gerenciar modelo\n"
    "Em toda conversa e em todo projeto, em toda tarefa, use a skill `gerenciar-modelo` "
    "(config em `~/.claude/gerenciar-modelo.json`; nunca use modelo fora de `modelos_permitidos`).\n"
    "Eu peço: economize tokens o tempo todo; divida as tarefas numa árvore de subagentes e sessões filhas "
    "ligadas, em modelos mais baratos, que fazem a parte delas e devolvem o resultado; troque de modelo "
    "sozinho, sem me avisar.\n"
    f"{FIM}\n"
)


def detectar_plano(conta=CONTA):
    """Lê só o tipo de organização do login do Claude Code (nada de token ou e-mail)."""
    try:
        dados = json.loads(conta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    tipo = str((dados.get("oauthAccount") or {}).get("organizationType") or "").lower()
    for plano in ("Ultra", "Max", "Enterprise", "Team", "Pro"):  # o mais específico primeiro
        if plano.lower() in tipo:
            return plano
    return "API" if dados.get("primaryApiKey") and not tipo else None


def modelos_do_plano(plano, tem_fable):
    base = ["haiku", "sonnet", "opus"]
    return base + ["fable"] if tem_fable and plano != "Pro" else base


def config(plano, modo, tem_fable, principal="opus"):
    permitidos = modelos_do_plano(plano, tem_fable)
    assert plano in PLANOS and modo in MODOS and principal in permitidos
    return {"plano": plano, "modo": modo, "modelo_principal": principal, "modelos_permitidos": permitidos}


def ler_json(arq):
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {}


def gravar_json(arq, dados):
    arq.parent.mkdir(parents=True, exist_ok=True)
    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def por_padrao(base, modelo):
    """Grava o modelo padrão das conversas novas no settings.json, sem tocar nas outras chaves."""
    arq = base / "settings.json"
    s = ler_json(arq)
    s["model"] = modelo
    gravar_json(arq, s)


def com_bloco(texto):
    return sem_bloco(texto).rstrip() + ("\n\n" if texto.strip() else "") + BLOCO


def sem_bloco(texto):
    if INICIO not in texto:
        return texto
    antes, resto = texto.split(INICIO, 1)
    depois = resto.split(FIM, 1)[1] if FIM in resto else ""
    return (antes.rstrip() + "\n" + depois.lstrip("\n")).strip() + "\n" if (antes + depois).strip() else ""


def perguntar(texto, opcoes):
    while True:
        try:
            r = input(f"{texto} [{'/'.join(opcoes)}]: ").strip().lstrip("﻿")  # PowerShell 5.1 manda BOM no pipe
        except EOFError:
            sys.exit("\nEntrada encerrada. Nada foi gravado.")
        for o in opcoes:
            if r.lower() == o.lower():
                return o
        print("  Resposta não reconhecida, tente de novo.")


def sim(texto):
    return perguntar(texto, ("s", "n")) == "s"


def instalar(base=CLAUDE, conta=CONTA):
    print("Instalador da skill gerenciar-modelo. Nada é gravado antes da sua confirmação final.\n")
    plano = detectar_plano(conta)
    if not (plano and sim(f"Detectei o plano {plano}. Está certo?")):
        plano = perguntar("Qual é o seu plano do Claude?", PLANOS)
    tem_fable = plano == "Ultra" or (plano != "Pro" and sim("Seu plano inclui o modelo Fable?"))
    opcoes = ("opus", "sonnet", "fable") if tem_fable else ("opus", "sonnet")
    principal = perguntar("Modelo da conversa principal, que começa o projeto e distribui as tarefas "
                          "(opus é o recomendado; sonnet gasta menos)", opcoes)
    modo = perguntar("Modo (os dois economizam sempre; economia usa Fable só em extrema necessidade; "
                     "performance pode delegar ao Fable e usa modelos mais fortes nas partes difíceis)", MODOS)
    cfg = config(plano, modo, tem_fable, principal)
    padrao_modelo = principal
    global_ = sim("Aplicar em TODAS as conversas (antigas quando forem retomadas, novas) e em todos os projetos, "
                  f"adicionando uma regra em {base / 'CLAUDE.md'}?")
    padrao = sim(f"Pôr {padrao_modelo} como modelo padrão das conversas novas, em {base / 'settings.json'}?")

    print("\nVai ser gravado:")
    print(f"  - skill em {base / 'skills' / 'gerenciar-modelo'}")
    print(f"  - config em {base / 'gerenciar-modelo.json'}: {json.dumps(cfg, ensure_ascii=False)}")
    if global_:
        print(f"  - regra no {base / 'CLAUDE.md'} (entre marcadores, removível com --desinstalar)")
    if padrao:
        print(f"  - \"model\": \"{padrao_modelo}\" no {base / 'settings.json'} (o valor antigo volta com --desinstalar)")
    print("A partir da instalação, toda tarefa é dividida em subagentes e sessões filhas mais baratas")
    print("(Haiku para buscar e ler, Sonnet para implementar), e a troca de modelo acontece sozinha, sem aviso.")
    if not sim("Autoriza a instalação?"):
        print("Nada foi gravado.")
        return False

    destino = base / "skills" / "gerenciar-modelo"
    destino.mkdir(parents=True, exist_ok=True)
    shutil.copy2(AQUI / "skill" / "SKILL.md", destino / "SKILL.md")
    antigo = ler_json(base / "gerenciar-modelo.json")
    if padrao:
        cfg["padrao_gravado"] = True
        # reinstalação: guarda o modelo de antes da PRIMEIRA instalação, não o que ela mesma pôs
        cfg["modelo_anterior"] = (antigo["modelo_anterior"] if antigo.get("padrao_gravado")
                                  else ler_json(base / "settings.json").get("model"))
        por_padrao(base, padrao_modelo)
    gravar_json(base / "gerenciar-modelo.json", cfg)
    if global_:
        md = base / "CLAUDE.md"
        md.write_text(com_bloco(md.read_text(encoding="utf-8") if md.exists() else ""), encoding="utf-8")
    print("Instalado. Vale a partir da próxima mensagem em cada conversa.")
    return True


def trocar_modo(modo, base=CLAUDE):
    arq = base / "gerenciar-modelo.json"
    if modo not in MODOS or not arq.exists():
        sys.exit(f"Modo inválido ou skill não instalada. Modos: {', '.join(MODOS)}")
    cfg = ler_json(arq)
    cfg["modo"] = modo
    gravar_json(arq, cfg)
    print(f"Modo agora: {modo}")


def trocar_principal(modelo, base=CLAUDE):
    arq = base / "gerenciar-modelo.json"
    cfg = ler_json(arq)
    if modelo not in cfg.get("modelos_permitidos", []):
        sys.exit(f"Modelo fora do plano ou skill não instalada. Permitidos: {cfg.get('modelos_permitidos')}")
    cfg["modelo_principal"] = modelo
    gravar_json(arq, cfg)
    if cfg.get("padrao_gravado"):
        por_padrao(base, modelo)
    print(f"Modelo principal agora: {modelo}")


def desinstalar(base=CLAUDE):
    if not sim("Remover a skill, a config e a regra do CLAUDE.md?"):
        return
    cfg = ler_json(base / "gerenciar-modelo.json")
    if cfg.get("padrao_gravado"):
        s = ler_json(base / "settings.json")
        if cfg.get("modelo_anterior"):
            s["model"] = cfg["modelo_anterior"]
        else:
            s.pop("model", None)
        gravar_json(base / "settings.json", s)
    shutil.rmtree(base / "skills" / "gerenciar-modelo", ignore_errors=True)
    (base / "gerenciar-modelo.json").unlink(missing_ok=True)
    md = base / "CLAUDE.md"
    if md.exists():
        md.write_text(sem_bloco(md.read_text(encoding="utf-8")), encoding="utf-8")
    print("Removido.")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--desinstalar"]:
        desinstalar()
    elif a[:1] == ["--modo"] and len(a) == 2:
        trocar_modo(a[1])
    elif a[:1] == ["--principal"] and len(a) == 2:
        trocar_principal(a[1])
    else:
        instalar()
