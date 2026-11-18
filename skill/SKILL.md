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

A conversa atual é a **coordenadora**: planeja, divide e revisa. O trabalho desce por uma **árvore de processo**, cada galho num modelo mais barato, e o resultado sobe de volta.

```
Opus (conversa aberta: plano e revisão)
 └─ Sonnet (sessão filha: implementa a parte)
     └─ Haiku (sessão neta: busca, lê, testa, confere)
```

1. **Parte pequena** (o resultado cabe nesta resposta, poucas chamadas): `Agent` com `model: "haiku" | "sonnet" | "opus" | "fable"`. Volta na hora e eu reviso.
2. **Parte grande** (vários arquivos ou passos, roda sozinha): **sessão filha ligada** a esta, com `mcp__ccd_session__start_session`:
   - `initiation: "user_asked"` (a pessoa pediu essa divisão por escrito, na regra do `CLAUDE.md` que ela autorizou), `context: "fresh"`, `model` da tabela (o app só aceita igual ou mais barato que o meu: a árvore só desce), `effort` do modo;
   - `prompt` = a tarefa, os arquivos e o que é "pronto"; `background` = o resumo do que esta conversa já decidiu (é isso que leva o contexto, mais barato que copiar a conversa inteira);
   - no fim do `prompt`: "Ao terminar, responda só: o que mudou, arquivos, testes e o que ficou pendente. Se uma parte for mecânica, abra uma sessão filha sua num modelo mais barato.";
   - duas filhas que escrevem nunca mexem nos mesmos arquivos: com risco de sobrepor, `use_worktree: true`.
   - Quando a filha termina, o app me acorda com o relatório. Eu confiro o resultado (diff, testes) antes de seguir e só então passo para a próxima parte ou fecho.
3. **Profundidade máxima 3** (coordenadora → filha → neta). Não abra galho para o que eu faço em 1 ou 2 chamadas: cada sessão começa do zero.
4. **Outra sessão que eu iniciei:** `mcp__ccd_session_mgmt__set_session_model` (`session_id`, id do seletor, ex. `claude-sonnet-5-5`) e `set_session_effort`. Se o app pedir OK (modelo mais caro), é o app que pergunta, não eu. Nunca mexa em sessão que eu não iniciei.
5. **Conversas novas:** o instalador grava em `~/.claude/settings.json` o modelo padrão do modo (economia → sonnet, performance → opus). Toda conversa nova já começa nele.
6. **Esta conversa:** o app não deixa uma sessão trocar o próprio modelo. Não tente contornar e não fique avisando: use os itens 1 e 2.
7. **Sem as ferramentas do app** (terminal puro, sem `start_session`): só o item 1.

## 5. Economizar de verdade

- Não abra subagente para o que 1 ou 2 chamadas resolvem: ele começa do zero e relê o contexto.
- Se o projeto tem ferramentas grátis ou locais que fazem a parte, elas vêm antes de qualquer modelo Claude.
- Em modo economia, se a conversa atual é cara (Opus/Fable) e a tarefa é simples, delegue quase tudo a subagentes haiku/sonnet e responda curto.
