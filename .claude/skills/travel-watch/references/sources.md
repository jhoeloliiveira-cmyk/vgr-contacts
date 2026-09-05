# Fontes e templates de URL

Datas em `YYYY-MM-DD` salvo onde indicado. Substitua os `{campos}`.

## Voos

| Fonte | URL |
|---|---|
| Google Flights | `https://www.google.com/travel/flights?q=Flights%20to%20{TO}%20from%20{FROM}%20on%20{YYYY-MM-DD}%20oneway&curr=GBP&hl=en-GB&gl=GB` |
| Skyscanner | `https://www.skyscanner.net/transport/flights/{from}/{to}/{YYMMDD}/?adultsv2=1&cabinclass=economy` |
| Kayak | `https://www.kayak.co.uk/flights/{FROM}-{TO}/{YYYY-MM-DD}?sort=price_a` |
| Momondo | `https://www.momondo.co.uk/flight-search/{FROM}-{TO}/{YYYY-MM-DD}?sort=price_a` |
| easyJet | `https://www.easyjet.com/en/buy/flights?dep={FROM}&arr={TO}&dd={YYYY-MM-DD}&apax=1` |
| British Airways | `https://www.britishairways.com/travel/book/public/en_gb` (form; scraping instavel) |
| TAP | `https://www.flytap.com/en-gb/` (form; scraping instavel) |

Skyscanner usa data no formato `YYMMDD` — 18/10/2026 vira `261018`.

## Hoteis

| Fonte | URL |
|---|---|
| Booking.com | `https://www.booking.com/searchresults.html?ss={cidade}&checkin={YYYY-MM-DD}&checkout={YYYY-MM-DD}&group_adults=1&no_rooms=1&order=price&selected_currency=GBP` |
| Hostelworld | `https://www.hostelworld.com/s?q={cidade}&from={YYYY-MM-DD}&to={YYYY-MM-DD}` |
| Google Hotels | `https://www.google.com/travel/hotels/{cidade}?q={cidade}&ts=...` (URL fragil, prefira Booking) |

Booking mostra o **total da estadia**, nao a diaria. Divida por `nights`
antes de falar em "diaria" — e diga qual dos dois voce esta reportando.

## Rota Londres -> Lisboa, o que esperar

- **Direto do LGW:** easyJet e British Airways. TAP opera majoritariamente do
  LHR; a operacao LGW e sazonal, entao confirme antes de prometer.
- **Outros aeroportos de Londres:** Ryanair voa STN/LTN -> LIS e costuma ter a
  tarifa base mais baixa da praca, mas some bagagem + traslado (Stansted
  Express ~£22 e ~50 min de Liverpool Street) antes de dizer que ficou barato.
- **Voo com conexao** (Vueling via BCN, Iberia via MAD) so vale se a diferenca
  for grande — dobra o tempo de porta a porta.
- Duracao do direto: ~2h35.

## Confiabilidade das fontes

Agregador entrega preco **indicativo**: bagagem, assento e taxa de cartao
aparecem so no checkout. Ao recomendar uma opcao, abra o site da companhia e
confirme o total final antes de dizer ao usuario que aquele e o preco.
