---
name: public-site-crawler-backpressure
description: Diagnosticar e conter tráfego automatizado num site público com renderização no servidor (SSR) que chama um backend com limites por visitante, como uma tempestade de 429, páginas com dados em falta ou um crawler que não abranda. Usa quando há volume anormal de pedidos ao backend vindo das páginas públicas; não para ataques DDoS de rede nem para limites de APIs privadas sem frontend.
---

# Crawlers, SSR e contrapressão

Um crawler não precisa de ser malicioso para derrubar um site recém-aberto.
O dano vem da **multiplicação**: cada página gerada no servidor faz várias
chamadas ao backend, e se o site esconder os limites do backend, o crawler
nunca sabe que deve abrandar.

## Reconhecer o padrão

- Muitas chamadas ao backend por minuto, a tickers, produtos ou páginas que
  vão mudando, com uma parte em `429`.
- Os IPs vistos pelo backend são os da plataforma de alojamento (saída
  serverless), não os dos visitantes. Se a prova do IP do visitante falhar,
  todos partilham o mesmo bucket; confirma isso primeiro (ver
  `clerk-fastapi-trust-boundaries`).
- As páginas devolvem `200` ao cliente com secções vazias ou mensagens como
  "temporarily unavailable", porque o erro do backend foi absorvido no SSR.
- Os logs da plataforma mostram poucos visitantes humanos e um User-Agent de
  crawler dominante. Os crawlers de IA usam frequentemente um User-Agent que
  começa como um browser normal e acrescenta o identificador do bot.

## Medir antes de corrigir

1. No backend, contar chamadas por rota e por minuto, e a proporção de `429`.
   Dividir pelo número de páginas geradas dá as **chamadas por página**.
2. Na plataforma (Vercel ou equivalente): rotas mais pedidas, códigos de
   resposta por rota, concentração por cliente (mascarada), User-Agents,
   Referers, e se há ISR, revalidação ou crons. Só agregados.
3. Distinguir três causas, que pedem correções diferentes:
   - **crawler distribuído** (muitos IPs, um User-Agent dominante);
   - **repetição em ciclo** no browser ou no SSR (o mesmo cliente e o mesmo
     recurso a intervalos curtos e regulares);
   - **trabalho da própria plataforma** (revalidação, pré-geração, crons).

## Porque é que os limites por IP não chegam

- Um crawler distribuído fica perto do limite em cada IP e gera milhares de
  pedidos no total.
- Os modos de desafio das plataformas costumam deixar passar **bots
  verificados**; não travam crawlers conhecidos.
- Mesmo quando o backend recusa, a página já foi gerada e as chamadas já
  foram feitas: o custo acontece na mesma.
- Se a página responde `200`, o crawler não recebe sinal para abrandar.

## Defesa por camadas

| Camada | Efeito |
| --- | --- |
| Bloqueio por User-Agent no firewall da plataforma | Os crawlers indesejados não chegam a gerar a página |
| `robots.txt` (e sitemap) | Os crawlers que cumprem as regras param antes de pedir; não é uma barreira de segurança |
| Propagar `429`/`503` com `Retry-After` | Quando o backend limita dados necessários, a página responde com esse código; crawlers legítimos abrandam |
| Repetições com backoff e limite | Sem ciclos: backoff exponencial com jitter, respeito por `Retry-After`, máximo de tentativas, nenhuma repetição automática no SSR depois de `429` |
| Menos chamadas por página e cache curta no servidor | Dados públicos que mudam pouco ficam em cache; secções secundárias carregam a pedido. Nunca guardar respostas autenticadas ou por utilizador |
| Limites no backend calibrados | O limite por visitante cobre uma visita humana normal (medida) e trava um cliente abusivo |

Decidir primeiro a política: que crawlers podem indexar (motores de busca)
e quais não (por exemplo, recolha para treino de IA quando os dados são
confidenciais ou licenciados). Essa decisão é do dono do produto.

## Verificar

- Depois de cada camada, voltar a medir as chamadas por minuto ao backend e a
  proporção de `429`, na mesma janela de comparação.
- Confirmar que um browser normal continua a abrir o site sem desafio
  visível e que as páginas autenticadas não foram afetadas.
- Um modo de desafio ativado sem queda de carga é evidência de que a fonte
  passa por ele (bot verificado ou tráfego interno), não de que funcionou.

## Quando não aplicar

Ataques volumétricos de rede (camadas 3 e 4) são do fornecedor de CDN/DDoS.
APIs sem frontend público usam autenticação e quotas próprias, não esta
receita.

## Evidência

Incidente observado a 26/10/2026, na abertura de um site Next.js com SSR no
Vercel, com backend FastAPI atrás de Cloudflare Access: um crawler de IA
verificado gerou ~92% do tráfego e ~26 000 chamadas por hora ao backend; o
Attack Challenge Mode não o travou e as páginas devolviam `200` com dados em
falta. Confirma os nomes das regras geridas e o tratamento de bots
verificados na documentação atual da plataforma.

## Relacionadas (leitura opcional, se disponíveis)

- `clerk-fastapi-trust-boundaries`: prova do IP do visitante entre o BFF e o backend.
- `public-projections-of-confidential-data`: o que expor sem sessão.
