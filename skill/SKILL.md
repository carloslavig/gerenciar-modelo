---
name: gerenciar-modelo
description: Economiza tokens o tempo todo escolhendo o modelo Claude certo (Haiku, Sonnet, Opus, Fable) para cada parte da tarefa e dividindo o trabalho numa árvore de sessões e subagentes mais baratos, conforme o plano da pessoa (Pro, Max, Team, Enterprise, API...) e o modo (economia ou performance). Use em TODA tarefa de construção, pesquisa ou mudança de código, ao delegar a subagente ou abrir sessão, e quando perguntarem "qual modelo uso?".
---

# Gerenciar modelo

A economia é **constante**: desde a instalação, toda tarefa passa por esta divisão. Não existe gatilho de uso nem "esperar gastar 70%".

## 1. Ler a configuração (sempre primeiro, sem comentar)

`~/.claude/gerenciar-modelo.json`, gravado pelo instalador com a autorização da pessoa:

```json
{"plano": "Pro", "modo": "economia", "modelos_permitidos": ["haiku", "sonnet", "opus"]}
```

- Sem o arquivo: a pessoa não autorizou. Não troque nada.
- **Nunca use modelo fora de `modelos_permitidos`.** Pro não tem Fable.
- Confira o plano ao vivo quando der: `mcp__ccd_session_mgmt__get_usage` → `plan.plan`. Se for diferente do arquivo, valha o mais restritivo; se o plano ao vivo for Pro, Fable fica proibido mesmo que o arquivo diga outra coisa.
- Uma chamada com modelo recusada pelo app ("modelo não disponível") = esse modelo não existe no plano: não tente de novo nesta conversa.
- Modo antigo `auto` vale como `economia`.

## 2. Os dois modos (os dois economizam)

**Economia (padrão):** cada parte no modelo mais barato que dá conta.
- Conversa principal: Sonnet (padrão das conversas novas).
- Fable só em **extrema necessidade** (o Opus já errou a mesma coisa duas vezes, ou a decisão pode causar perda de dinheiro, de dados ou falha de segurança) **e** se o plano permitir.

**Performance:** gasta mais para render mais, sem desperdiçar.
- Conversa principal: Opus, ou Fable se o plano permitir.
- Pode delegar a Fable (filhas ou subagentes) as partes difíceis.
- A árvore continua: busca e leitura seguem no Haiku, implementação no Sonnet.

Se a pessoa disser "modo economia" ou "modo performance" na conversa, vale para aquela conversa. Para mudar de vez: `python instalar.py --modo <modo>`.

## 3. Qual modelo para cada parte

| Tipo de trabalho | economia | performance |
|---|---|---|
| buscar, ler, listar, extrair, resumir, conferir, rodar teste | haiku | haiku |
| implementar, editar código, escrever texto | sonnet | sonnet |
| bug difícil, arquitetura, mudança em vários módulos, plano longo | sonnet → opus se falhar | opus |
| decisão cara de errar, pesquisa longa e autônoma | opus (fable só em extrema necessidade) | fable, senão opus |

Modelo da tabela fora de `modelos_permitidos` → o mais próximo abaixo.
Esforço: economia `low` em pergunta e `medium` no resto; performance `medium`, `high` no difícil. `xhigh`/`max` só se a pessoa pedir.

## 4. A árvore de processo (automática e calada)

A pessoa autorizou na instalação: **divida e troque sozinho, sem avisar e sem pedir confirmação.** Não escreva "vou usar o modelo X".

```
principal (coordena: plano, divisão, revisão)
 ├─ Haiku  (busca e lê o que a principal precisa saber)
 └─ Sonnet (implementa a parte)
     └─ Haiku (testa, confere, procura)
```

Fluxo de toda tarefa que não se resolve em 1 ou 2 chamadas:
1. **Levantar com Haiku:** busca e leitura de arquivos vão a um `Agent` com `model: "haiku"` (tipo `Explore` quando for só achar código). A principal recebe só a conclusão, não o arquivo inteiro.
2. **Fazer no modelo da tabela:**
   - parte pequena (o resultado cabe nesta resposta): `Agent` com o `model` da tabela;
   - parte grande (vários arquivos ou passos): **sessão filha ligada**, `mcp__ccd_session__start_session` com `initiation: "user_asked"` (pedido por escrito na regra do `CLAUDE.md` que a pessoa autorizou), `context: "fresh"`, `model` e `effort` da tabela. `prompt` = tarefa, arquivos e o que é "pronto"; `background` = resumo do que já foi decidido. No fim do `prompt`: "Ao terminar, responda só: o que mudou, arquivos, testes e pendências. Busca, leitura e teste vão a subagente Haiku; parte grande e separável vira sessão filha sua num modelo igual ou mais barato."
3. **Devolver e conferir:** quando a filha termina, o app acorda a principal com o relatório. A principal confere (diff, testes) e passa para a próxima parte.

Regras da árvore:
- Só desce: filha usa modelo igual ou mais barato que a mãe (o app recusa o contrário).
- No máximo 3 níveis. Cada sessão e subagente começa do zero: nunca abra galho para o que se faz em 1 ou 2 chamadas.
- Duas filhas que escrevem não mexem nos mesmos arquivos; com risco de sobrepor, `use_worktree: true`.
- Outra sessão que eu iniciei pode trocar de modelo com `mcp__ccd_session_mgmt__set_session_model` / `set_session_effort`. Nunca mexa em sessão que eu não iniciei.
- A conversa aberta não troca o próprio modelo (o app bloqueia). Não tente contornar e não avise: a árvore faz a economia.
- Sem as ferramentas do app (terminal puro): só subagentes.

## 5. Economia que vale em qualquer modo

- Ferramentas grátis ou locais do projeto vêm antes de qualquer modelo Claude.
- Respostas curtas na principal; o detalhe fica nos arquivos e nos relatórios das filhas.
- Não releia o que um subagente já resumiu.
