# gerenciar-modelo

Skill para o [Claude Code](https://claude.com/claude-code) que escolhe sozinha o modelo Claude (Haiku, Sonnet, Opus, Fable) para cada parte da tarefa, de acordo com o seu plano e quanto você ainda pode gastar.

- **Detecta o plano:** o instalador lê o tipo de plano do seu login do Claude Code (Pro, Max, Team, Enterprise ou API, sem ler token nem e-mail) e pede para você confirmar. No app desktop a skill confere de novo a cada tarefa. No Pro nunca usa o Fable.
- **Economiza sempre:** desde a instalação, toda tarefa é dividida. Não existe gatilho de uso.
- **Dois modos:**
  - `economia` (padrão): conversa principal no Sonnet, Opus quando o problema é difícil, e Fable só em extrema necessidade e se o plano permitir.
  - `performance`: conversa principal no Opus, ou no Fable se o plano permitir, e pode delegar ao Fable. Gasta mais, mas busca e leitura continuam no Haiku.
- **Automático e calado:** depois que você autoriza, a troca acontece sem aviso. As partes da tarefa vão para subagentes no modelo certo, sessões novas já abrem no modelo certo, e o modelo padrão das conversas novas segue o modo.
- **Árvore de processo:** a conversa aberta coordena. Uma parte grande vira uma sessão filha ligada a ela num modelo mais barato (Opus → Sonnet → Haiku). A filha faz a parte, pode abrir a própria filha para o trabalho mecânico e devolve o relatório. A coordenadora confere e segue. Partes pequenas vão para subagentes.
- **Vale para tudo:** conversas novas, conversas antigas quando você as retoma, e todos os projetos (pela regra no `~/.claude/CLAUDE.md`).

## Instalar

```bash
git clone https://github.com/carloslavig/gerenciar-modelo
cd gerenciar-modelo
python instalar.py
```

O instalador pergunta o plano, se o plano tem Fable, o modo, se vale para todas as conversas e projetos, e se pode trocar o modelo padrão. Depois mostra tudo o que vai gravar e só grava se você confirmar.

O que é gravado:
- `~/.claude/skills/gerenciar-modelo/SKILL.md`
- `~/.claude/gerenciar-modelo.json` (plano, modo, modelos permitidos)
- uma regra entre marcadores no `~/.claude/CLAUDE.md` (opcional)
- `"model"` no `~/.claude/settings.json` (opcional; o valor antigo fica guardado)

## Trocar o modo ou remover

```bash
python instalar.py --modo economia
python instalar.py --desinstalar
```

A desinstalação apaga a skill e a config, tira a regra do `CLAUDE.md` e devolve o modelo padrão que você tinha antes.

## Limite conhecido

O Claude Code não deixa uma conversa trocar o próprio modelo no meio dela, para o custo não mudar sem você ver. Por isso a conversa aberta fica no modelo dela e o resto desce pela árvore. As sessões filhas só podem usar modelo igual ou mais barato que a mãe. A árvore de sessões precisa do app desktop do Claude Code; no terminal puro só há subagentes.

## Testes

```bash
python -m pytest -q
```

Licença MIT.
