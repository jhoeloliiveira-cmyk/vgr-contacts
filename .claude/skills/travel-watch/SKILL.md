---
name: travel-watch
description: Monitora preço de voos e hotéis para uma viagem específica e avisa quando cai. Use quando o usuário pedir para pesquisar, acompanhar, monitorar ou "ficar de olho" em passagem aérea, voo, hotel, hospedagem ou diária — ex. "acha o voo mais barato de Londres pra Lisboa", "monitora hotel em Londres dia 16 a 18", "avisa se a passagem baixar", "roda o travel watch", "checa os preços da viagem". Cobre busca pontual (preço agora) e monitoramento recorrente com histórico e alerta de queda.
---

# Travel Watch — monitor de voo + hotel

Acompanha o preço de um ou mais trechos aéreos e de hospedagem, guarda
histórico a cada checagem e avisa quando o preço cai abaixo de um alvo.

## Fluxo

1. Leia `watchlist.json` (na raiz da skill). Ele define o que monitorar.
   Se o usuário pedir um destino que não está lá, adicione uma entrada nova.
2. Colete os preços — use a **escada de fontes** abaixo, na ordem.
3. Grave o resultado com `scripts/history.mjs record`.
4. Reporte: preço atual, variação desde a última checagem, mínimo histórico,
   e se bateu o `targetPrice`.

## Escada de fontes (pare no primeiro degrau que funcionar)

Ambientes diferentes têm redes diferentes. Sempre tente nesta ordem e
**diga no relatório qual degrau produziu o número** — isso define a confiança.

### Degrau 1 — scraping direto (preço exato, alta confiança)

```bash
node .claude/skills/travel-watch/scripts/check.mjs flights --from LGW --to LIS --date 2026-10-18
node .claude/skills/travel-watch/scripts/check.mjs hotels --city London --checkin 2026-10-16 --checkout 2026-10-18
```

Requer Playwright + Chromium e saída de rede para `google.com` / `booking.com`.
O script sai com código `3` e imprime `BLOCKED:` se a rede barrar — nesse caso
**não insista, não tente `curl`**: desça para o degrau 2.

### Degrau 2 — WebFetch nas páginas com data na URL (preço exato, média confiança)

Use os templates de `references/sources.md`. Peça no prompt do WebFetch:
"extraia companhia, horário e preço; se a página estiver bloqueada ou sem
preços responda exatamente NO DATA".

### Degrau 3 — WebSearch (só ordem de grandeza, baixa confiança)

WebSearch devolve médias de rota ("a partir de £39"), **não** o preço da sua
data. Quando só o degrau 3 responder, rotule o número como estimativa e diga
explicitamente que não é a tarifa da data pedida. Nunca apresente uma média de
rota como se fosse o preço do voo.

> Se todos os três degraus falharem, diga isso. Um "não consegui o preço" é um
> resultado válido; um preço inventado não é.

## Regras de honestidade

- Nunca combine números de moedas diferentes sem converter e dizer a taxa.
- Ida-e-volta e só-ida não são comparáveis: rotule sempre.
- Preço de agregador é indicativo — o preço final só existe no checkout da
  companhia, com bagagem e assento incluídos. Diga isso quando recomendar.
- Se a fonte não trouxer a data pedida, isso é ausência de dado, não um preço.

## Bagagem muda a comparação

Em rota de baixo custo (easyJet, Ryanair, Vueling, Wizz) a tarifa base é só
mochila de baixo do assento. Ao comparar com BA/TAP — que costumam incluir mala
de mão de 10 kg no porta-malas — some o extra de bagagem antes de dizer qual é
o mais barato. `watchlist.json` tem `baggage` para registrar o que você precisa.

## Histórico e alerta

```bash
# grava uma leitura
node .claude/skills/travel-watch/scripts/history.mjs record --key flight:LGW-LIS:2026-10-18 \
  --price 78.99 --currency GBP --label "easyJet 06:25" --source gflights

# resumo com variação, mínimo e status do alvo
node .claude/skills/travel-watch/scripts/history.mjs report --key flight:LGW-LIS:2026-10-18 --target 70
node .claude/skills/travel-watch/scripts/history.mjs report --all
```

O histórico fica em `.claude/skills/travel-watch/data/history.json`, versionado
no git — o gráfico de preço só existe se as leituras forem commitadas. Faça
commit depois de gravar.

## Ao rodar como rotina

Sem interação humana. Colete, grave, commite e então:

- Preço **abaixo do `targetPrice`** ou queda ≥ 10% desde a última leitura →
  notifique (e-mail via Gmail, ou o canal em `notify` do watchlist).
- Nada relevante mudou → apenas commite o histórico, **sem** notificar.

Alerta que dispara todo dia deixa de ser alerta.
