"""Instala a skill gerenciar-modelo no Claude Code, pedindo autorização a cada passo.

Uso:
  python instalar.py               instala (pergunta tudo antes de gravar)
  python instalar.py --modo auto   troca só o modo (economia | performance | auto)
  python instalar.py --desinstalar remove tudo o que o instalador gravou
"""
import json
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CLAUDE = Path.home() / ".claude"
MODOS = ("economia", "performance", "auto")
PLANOS = ("Pro", "Max", "Team", "Enterprise", "API")
INICIO = "<!-- gerenciar-modelo:inicio -->"
FIM = "<!-- gerenciar-modelo:fim -->"
BLOCO = (
    f"{INICIO}\n"
    "# Gerenciar modelo\n"
    "Em toda conversa e em todo projeto, antes de delegar a subagente, abrir sessão nova "
    "ou começar tarefa de construção, use a skill `gerenciar-modelo` "
    "(config em `~/.claude/gerenciar-modelo.json`; nunca use modelo fora de `modelos_permitidos`).\n"
    "Eu peço: divida as tarefas grandes em sessões filhas ligadas, em modelos mais baratos, que fazem a parte "
    "delas e devolvem o resultado; troque de modelo sozinho, sem me avisar.\n"
    f"{FIM}\n"
)


def modelos_do_plano(plano, tem_fable):
    base = ["haiku", "sonnet", "opus"]
    return base + ["fable"] if tem_fable and plano != "Pro" else base


def config(plano, modo, tem_fable, limite=70):
    assert plano in PLANOS and modo in MODOS
    return {"plano": plano, "modo": modo, "modelos_permitidos": modelos_do_plano(plano, tem_fable),
            "limite_economia": limite}


def modelo_padrao(modo):
    return "opus" if modo == "performance" else "sonnet"


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


def instalar(base=CLAUDE):
    print("Instalador da skill gerenciar-modelo. Nada é gravado antes da sua confirmação final.\n")
    plano = perguntar("Qual é o seu plano do Claude?", PLANOS)
    tem_fable = plano != "Pro" and sim("Seu plano inclui o modelo Fable?")
    modo = perguntar("Modo (economia gasta menos; performance prioriza qualidade; auto troca sozinho pelo uso)", MODOS)
    cfg = config(plano, modo, tem_fable)
    global_ = sim("Aplicar em TODAS as conversas (antigas quando forem retomadas, novas) e em todos os projetos, "
                  f"adicionando uma regra em {base / 'CLAUDE.md'}?")
    padrao = sim(f"Trocar sozinho o modelo padrão das conversas novas conforme o modo (agora: {modelo_padrao(modo)}), "
                 f"em {base / 'settings.json'}?")

    print("\nVai ser gravado:")
    print(f"  - skill em {base / 'skills' / 'gerenciar-modelo'}")
    print(f"  - config em {base / 'gerenciar-modelo.json'}: {json.dumps(cfg, ensure_ascii=False)}")
    if global_:
        print(f"  - regra no {base / 'CLAUDE.md'} (entre marcadores, removível com --desinstalar)")
    if padrao:
        print(f"  - \"model\": \"{modelo_padrao(modo)}\" no {base / 'settings.json'} (o valor antigo volta com --desinstalar)")
    print("A troca de modelo acontece sozinha, sem avisar a cada vez.")
    if global_:
        print("Tarefas grandes viram sessões filhas ligadas à conversa, em modelos mais baratos, que devolvem o resultado.")
    if not sim("Autoriza a instalação?"):
        print("Nada foi gravado.")
        return False

    destino = base / "skills" / "gerenciar-modelo"
    destino.mkdir(parents=True, exist_ok=True)
    shutil.copy2(AQUI / "skill" / "SKILL.md", destino / "SKILL.md")
    if padrao:
        cfg["padrao_gravado"] = True
        cfg["modelo_anterior"] = ler_json(base / "settings.json").get("model")
        por_padrao(base, modelo_padrao(modo))
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
    if cfg.get("padrao_gravado"):
        por_padrao(base, modelo_padrao(modo))
    print(f"Modo agora: {modo}")


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
    else:
        instalar()
