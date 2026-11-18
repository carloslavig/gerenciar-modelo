import builtins
import json

import instalar as i


def test_pro_nunca_tem_fable():
    assert "fable" not in i.config("Pro", "economia", tem_fable=True)["modelos_permitidos"]
    assert "fable" in i.config("Max", "economia", tem_fable=True)["modelos_permitidos"]


def test_modelo_padrao_por_modo():
    assert i.modelo_padrao("economia", ["haiku", "sonnet", "opus", "fable"]) == "sonnet"
    assert i.modelo_padrao("performance", ["haiku", "sonnet", "opus", "fable"]) == "fable"
    assert i.modelo_padrao("performance", ["haiku", "sonnet", "opus"]) == "opus"


def test_detecta_plano(tmp_path):
    conta = tmp_path / "c.json"
    for tipo, plano in [("claude_pro", "Pro"), ("claude_max", "Max"), ("claude_team", "Team"),
                        ("claude_enterprise", "Enterprise")]:
        conta.write_text(json.dumps({"oauthAccount": {"organizationType": tipo}}), encoding="utf-8")
        assert i.detectar_plano(conta) == plano
    conta.write_text(json.dumps({"primaryApiKey": "x"}), encoding="utf-8")
    assert i.detectar_plano(conta) == "API"
    assert i.detectar_plano(tmp_path / "nao-existe.json") is None


def test_bloco_idempotente_e_removivel():
    original = "# minhas regras\n"
    uma = i.com_bloco(original)
    assert i.com_bloco(uma) == uma
    assert i.sem_bloco(uma).strip() == original.strip()
    assert i.sem_bloco(i.com_bloco("")) == ""


def _responder(monkeypatch, respostas):
    it = iter(respostas)
    monkeypatch.setattr(builtins, "input", lambda _: next(it))


def test_bom_do_powershell_e_ignorado(monkeypatch):
    _responder(monkeypatch, ["﻿Pro"])
    assert i.perguntar("plano?", i.PLANOS) == "Pro"


def test_recusa_nao_grava_nada(tmp_path, monkeypatch):
    base = tmp_path / "claude"
    _responder(monkeypatch, ["Pro", "economia", "s", "s", "n"])
    assert i.instalar(base, tmp_path / "sem-conta.json") is False
    assert not base.exists()


def test_instala_reinstala_e_desinstala(tmp_path, monkeypatch):
    base = tmp_path / "claude"
    base.mkdir()
    conta = tmp_path / "c.json"
    conta.write_text(json.dumps({"oauthAccount": {"organizationType": "claude_max"}}), encoding="utf-8")
    (base / "CLAUDE.md").write_text("# regras antigas\n", encoding="utf-8")
    (base / "settings.json").write_text('{"model": "haiku", "theme": "dark"}', encoding="utf-8")

    # plano detectado (s), tem Fable (s), performance, global (s), padrão (s), autoriza (s)
    _responder(monkeypatch, ["s", "s", "performance", "s", "s", "s"])
    assert i.instalar(base, conta)
    cfg = i.ler_json(base / "gerenciar-modelo.json")
    assert cfg["plano"] == "Max" and "fable" in cfg["modelos_permitidos"]
    assert i.ler_json(base / "settings.json") == {"model": "fable", "theme": "dark"}
    assert i.INICIO in (base / "CLAUDE.md").read_text(encoding="utf-8")

    i.trocar_modo("economia", base)
    assert i.ler_json(base / "settings.json")["model"] == "sonnet"

    # reinstalar não perde o modelo de antes da primeira instalação
    _responder(monkeypatch, ["s", "s", "economia", "s", "s", "s"])
    assert i.instalar(base, conta)
    assert i.ler_json(base / "gerenciar-modelo.json")["modelo_anterior"] == "haiku"

    _responder(monkeypatch, ["s"])
    i.desinstalar(base)
    assert not (base / "gerenciar-modelo.json").exists()
    assert i.ler_json(base / "settings.json") == {"model": "haiku", "theme": "dark"}
    assert (base / "CLAUDE.md").read_text(encoding="utf-8").strip() == "# regras antigas"
