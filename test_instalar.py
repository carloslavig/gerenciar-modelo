import builtins
import json

import instalar as i


def test_pro_nunca_tem_fable():
    assert "fable" not in i.config("Pro", "auto", tem_fable=True)["modelos_permitidos"]
    assert "fable" in i.config("Max", "auto", tem_fable=True)["modelos_permitidos"]


def test_bloco_idempotente_e_removivel():
    original = "# minhas regras\n"
    uma = i.com_bloco(original)
    assert i.com_bloco(uma) == uma
    assert i.sem_bloco(uma).strip() == original.strip()
    assert i.sem_bloco(i.com_bloco("")) == ""


def _responder(monkeypatch, respostas):
    it = iter(respostas)
    monkeypatch.setattr(builtins, "input", lambda _: next(it))


def test_recusa_nao_grava_nada(tmp_path, monkeypatch):
    _responder(monkeypatch, ["Pro", "economia", "s", "s", "n"])
    assert i.instalar(tmp_path) is False
    assert list(tmp_path.iterdir()) == []


def test_instala_e_desinstala(tmp_path, monkeypatch):
    (tmp_path / "CLAUDE.md").write_text("# regras antigas\n", encoding="utf-8")
    (tmp_path / "settings.json").write_text('{"model": "haiku", "theme": "dark"}', encoding="utf-8")
    _responder(monkeypatch, ["Max", "s", "performance", "s", "s", "s"])
    assert i.instalar(tmp_path)
    cfg = json.loads((tmp_path / "gerenciar-modelo.json").read_text(encoding="utf-8"))
    assert cfg["modo"] == "performance" and "fable" in cfg["modelos_permitidos"]
    assert (tmp_path / "skills/gerenciar-modelo/SKILL.md").exists()
    assert i.INICIO in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")

    assert i.ler_json(tmp_path / "settings.json") == {"model": "opus", "theme": "dark"}

    i.trocar_modo("economia", tmp_path)
    assert json.loads((tmp_path / "gerenciar-modelo.json").read_text(encoding="utf-8"))["modo"] == "economia"
    assert i.ler_json(tmp_path / "settings.json")["model"] == "sonnet"

    _responder(monkeypatch, ["s"])
    i.desinstalar(tmp_path)
    assert not (tmp_path / "gerenciar-modelo.json").exists()
    assert i.ler_json(tmp_path / "settings.json") == {"model": "haiku", "theme": "dark"}
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8").strip() == "# regras antigas"
