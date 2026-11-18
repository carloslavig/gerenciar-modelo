---
name: gerenciar-modelo
description: Escolhe o modelo Claude certo (Haiku, Sonnet, Opus, Fable) para cada parte de uma tarefa, respeitando o plano da pessoa (Pro, Max, Team, API) e quanto ela ainda pode gastar, em modo economia, performance ou automático. Use no começo de toda tarefa de construção, ao delegar a subagente ou abrir sessão nova, quando perguntarem "qual modelo uso?", ou quando a tarefa ficar bem mais simples ou bem mais difícil do que o modelo atual pede.
---

# Gerenciar modelo

## 1. Ler a configuração (sempre primeiro)

Arquivo `~/.claude/gerenciar-modelo.json`, gravado pelo instalador com a autorização da pessoa:

```json
{"plano": "Pro", "modo": "auto", "modelos_permitidos": ["haiku", "sonnet", "opus"], "limite_economia": 70}
```

- **Nunca use modelo fora de `modelos_permitidos`.** No Pro não há Fable: nunca proponha nem abra nada com Fable.
- Sem o arquivo: a pessoa não autorizou a instalação. Não troque nada.
- Se a ferramenta `mcp__ccd_session_mgmt__get_usage` existir (app desktop), leia `plan.plan` e o `percentUsed` de cada janela, sem comentar. Se o plano lido for diferente do arquivo, siga o mais restritivo dos dois.

## 2. Escolher o modo

- `economia`: sempre o mais barato que dá conta.
- `performance`: qualidade primeiro, dentro dos modelos permitidos.
- `auto` (padrão): `performance` enquanto todas as janelas de uso estão abaixo de `limite_economia`%; `economia` quando qualquer uma passa.

Se a pessoa disser "modo economia" ou "modo performance" na conversa, vale para aquela conversa sem mexer no arquivo. Para mudar de vez: `python instalar.py --modo <modo>` (ou editar o JSON).

## 3. Qual modelo para cada parte

| Tipo de trabalho | economia | performance |
|---|---|---|
| buscar, ler, listar, extrair, resumir, conferir formato | haiku | haiku |
| programar no dia a dia, editar código conhecido, testes, textos | haiku → sonnet se falhar | sonnet |
| bug difícil, arquitetura, mudança em vários módulos, plano longo | sonnet → opus se falhar | opus |
| decisão cara de errar (dinheiro, dados, segurança), pesquisa longa autônoma | opus | fable (se permitido), senão opus |

Se o modelo da tabela não está em `modelos_permitidos`, use o mais próximo abaixo dele; sem nenhum abaixo, o mais barato permitido.

Esforço (`effort`): economia usa `low` em pergunta e `medium` no resto; performance usa `medium`, e `high` no difícil. `xhigh`/`max` só se a pessoa pedir.

## 4. Como trocar (automático e calado)

A pessoa já autorizou na instalação: **troque sozinho, sem avisar e sem pedir confirmação**. Não escreva "vou usar o modelo X" nem relatório de modelos.

1. **Subagente (o jeito principal):** a conversa atual é a coordenadora. Mande cada parte, pelo tipo da tabela, a um `Agent` com `model: "haiku" | "sonnet" | "opus" | "fable"` e revise o que voltar. Assim o trabalho roda no modelo certo sem trocar a conversa.
2. **Sessão nova:** `mcp__ccd_session__start_session` com o `model` da tabela.
3. **Outra sessão que eu iniciei:** `mcp__ccd_session_mgmt__set_session_model` (`session_id`, id do seletor, ex. `claude-sonnet-5-5`) e `set_session_effort`. Se o app pedir OK (modelo mais caro), é o app que pergunta, não eu. Nunca mexa em sessão que eu não iniciei.
4. **Conversas novas:** o instalador grava em `~/.claude/settings.json` o modelo padrão do modo (economia → sonnet, performance → opus). Toda conversa nova já começa nele.
5. **Esta conversa:** o app não deixa uma sessão trocar o próprio modelo. Não tente contornar e não fique avisando: use o item 1.

## 5. Economizar de verdade

- Não abra subagente para o que 1 ou 2 chamadas resolvem: ele começa do zero e relê o contexto.
- Se o projeto tem ferramentas grátis ou locais que fazem a parte, elas vêm antes de qualquer modelo Claude.
- Em modo economia, se a conversa atual é cara (Opus/Fable) e a tarefa é simples, delegue quase tudo a subagentes haiku/sonnet e responda curto.
