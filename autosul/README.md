# Autosul — UTM do formulário da LP

Três links rastreados (Nedja, seu Biu e Renan) + a ponte que faz a UTM
sobreviver da URL até o envio do formulário.

## Os 3 links

Troque `SEU-DOMINIO` pela URL real da LP. O resto vai exatamente como está:
UTM é case-sensitive, então `Nedja` e `nedja` viram duas linhas diferentes
no relatório.

**Nedja**

```
https://SEU-DOMINIO/?utm_source=vendedor&utm_medium=indicacao&utm_campaign=autosul&utm_content=nedja
```

**Seu Biu**

```
https://SEU-DOMINIO/?utm_source=vendedor&utm_medium=indicacao&utm_campaign=autosul&utm_content=seu-biu
```

**Renan**

```
https://SEU-DOMINIO/?utm_source=vendedor&utm_medium=indicacao&utm_campaign=autosul&utm_content=renan
```

### Por que esses valores

| Parâmetro      | Valor                        | Papel |
| -------------- | ---------------------------- | ----- |
| `utm_source`   | `vendedor`                   | De onde vem o tráfego. `vendedor` funciona em qualquer canal — se um dia quiserem separar, é só trocar por `whatsapp` ou `instagram`. |
| `utm_medium`   | `indicacao`                  | Tipo de tráfego. Separa o time de vendas de anúncio pago e orgânico. |
| `utm_campaign` | `autosul`                    | A campanha. Se rodar por safra, use `autosul-2026`. |
| `utm_content`  | `nedja` / `seu-biu` / `renan`| **Quem mandou o link.** É por aqui que se conta lead por vendedor. |

Para incluir mais gente depois, é só repetir o link mudando o `utm_content`.
Regra: minúsculo, sem acento, sem espaço (use hífen).

## A ponte

O problema: a UTM vive na URL. A pessoa abre a LP, navega para outra
página, recarrega, volta meia hora depois — e a URL já não tem mais nada.
Se o formulário só lê a URL no momento do envio, metade dos leads chega
sem origem.

O `utm-bridge.js` resolve isso:

```
link do vendedor          LP                      lead
─────────────────────────────────────────────────────────────
?utm_content=nedja  →  lê a URL
                       guarda por 30 dias (localStorage)
                       ↓
                       sobrevive a reload, a troca de página
                       e a visita nova sem query string
                       ↓
                       preenche <input hidden> em todo <form>
                                               →  utm_content=nedja
                                                  chega junto com
                                                  nome e telefone
```

### Instalação

1. Suba `utm-bridge.js` na LP (ex.: `/js/utm-bridge.js`).
2. Antes do `</body>`:

```html
<script src="/js/utm-bridge.js" defer></script>
```

Só isso. O script acha os formulários sozinho e cria os campos ocultos —
não precisa mexer no HTML do form.

Se preferirem deixar os campos explícitos (fica mais claro para quem
mexer no form depois), funciona igual — o script preenche os que já
existem em vez de criar:

```html
<form action="/enviar" method="post">
  <input name="nome" placeholder="Nome">
  <input name="telefone" placeholder="Telefone">

  <input type="hidden" name="utm_source">
  <input type="hidden" name="utm_medium">
  <input type="hidden" name="utm_campaign">
  <input type="hidden" name="utm_content">

  <button type="submit">Enviar</button>
</form>
```

### O que chega no lead

Além dos quatro `utm_*`, a ponte manda:

| Campo            | Para quê |
| ---------------- | -------- |
| `utm_term`       | Preenchido só se o link tiver. |
| `gclid`, `fbclid`| Clique de Google Ads / Meta Ads, quando houver. |
| `pagina_entrada` | Por qual página a pessoa entrou. |
| `referrer`       | De qual site veio. |
| `data_clique`    | Quando clicou no link (ISO 8601). |

Quem recebe o lead (e-mail, CRM, planilha) precisa aceitar esses campos
— se o backend valida campo por campo, inclua-os na lista permitida,
senão o envio é rejeitado ou os valores são descartados em silêncio.

### Se o formulário envia JSON (React, fetch, AJAX)

Campo oculto criado fora do React não entra num payload montado pelo
estado do componente. Nesse caso, pegue os valores direto:

```js
fetch('/api/lead', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ ...dadosDoForm, ...window.AutosulUTM.get() })
});
```

### CTA de WhatsApp (opcional)

Se o botão principal da LP for WhatsApp, marque o link:

```html
<a href="https://wa.me/5581999999999?text=Quero%20saber%20mais" data-utm-whatsapp>
  Falar no WhatsApp
</a>
```

A mensagem chega como `Quero saber mais [origem: nedja]` — quem atende já
sabe de qual link veio, sem depender do formulário. **O cliente enxerga
esse texto** e pode apagar antes de enviar; se preferirem algo discreto,
troque `[origem: ' + marca + ']` por um código curto (ex.: `#nd`) na
função `marcarWhatsapp`.

## Decisões embutidas no script

- **Último clique vence.** Se o cliente entrou pelo link da Nedja e uma
  semana depois voltou pelo do Renan, o lead sai como `renan`. É o
  critério justo quando cada vendedor divulga o seu. Para travar no
  primeiro, mude `ATRIBUICAO` para `'primeiro'` no topo do arquivo.
- **Janela de 30 dias.** Depois disso o lead volta a contar como sem
  origem. Ajuste em `VALIDADE_MS`.
- **Nunca sobrescreve o que a pessoa digitou** — só campos ocultos ou
  vazios.
- **Não vaza parâmetro para fora.** A UTM é propagada só em links do
  mesmo domínio.
- **Sem UTM nenhuma, o form continua normal** — não inventa origem falsa.
- **Storage bloqueado** (aba anônima, cookies negados) não quebra nada: a
  UTM segue valendo na sessão, só não sobrevive ao fechar o navegador.

## Como testar antes de publicar

1. Abra o link da Nedja na LP.
2. Console do navegador: `AutosulUTM.get()` → tem que mostrar
   `utm_content: "nedja"`.
3. Navegue para outra página da LP e rode de novo — tem que continuar
   `nedja`.
4. Envie o formulário com dados de teste e confira se `utm_content`
   chegou no destino (e-mail/CRM/planilha).
5. Só depois disso mande os links para o time.

No GA4 os leads aparecem em **Aquisição → Aquisição de tráfego**, com
`utm_content` disponível como dimensão "Conteúdo manual".
