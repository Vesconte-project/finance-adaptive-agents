---
name: public-projections-of-confidential-data
description: Desenhar ou rever a versão sem sessão (ou de um escalão inferior) de uma vista construída sobre um dataset agregado confidencial, como um mapa de relações, grafo, ranking, matriz de correlações ou embedding, quando o produto quer mostrar a forma sem permitir extrair os dados. Usa ao abrir rotas a anónimos, ao definir o que cada escalão recebe ou ao avaliar riscos de scraping. Não para controlo de acesso genérico nem para rate limiting isolado.
---

# Uma projeção pública tem um contrato de divulgação

Um produto quer muitas vezes mostrar uma vista "de montra" a quem não tem conta:
o mapa, as zonas, os nomes principais. O valor do produto está no dataset por
baixo. Começa por acordar **o que é confidencial**: relações, pesos, pertenças a grupos,
agregados, posições e atributos derivados podem ter políticas diferentes. Define o
atacante, informação auxiliar disponível e o que pode sair por escalão. Só depois
decide os campos e verifica a divulgação acumulada entre respostas.

Relato de origem: desenho de um atlas semanal de relações entre empresas em
18/10/2026 (cerca de 650 empresas e 25 zonas, com correlações de retornos
residuais). Foi relatada reconstrução superior a 60% das ligações com posições
reais. O artefacto, a métrica, o denominador e o protocolo não acompanham este
pacote: é um relato por confirmar, não uma medição reproduzida nem uma taxa
transferível. Para o citar como resultado, recuperar esses elementos.

## Os limites por IP não protegem o dataset

Limites por IP e caches travam curiosos e custos, não quem quer extrair: trocar
de IP é barato. Se uma única resposta anónima traz o grafo inteiro com pesos, ou
se percorrer todas as entidades traz todas as ligações, os limites só atrasam.
Desenha a **projeção** primeiro; os limites são uma segunda camada.

## Fugas que não parecem fugas

As restrições seguintes são exemplos para uma política que protege ligações e
composição detalhada. Não as adotes automaticamente: até contagens, nomes de
grupos e layouts esquemáticos podem divulgar informação não autorizada. Avalia
também grupos pequenos, cruzamentos e diferenças entre versões.

- **Valores por par:** correlações, distâncias, pesos de ligação, mesmo
  arredondados. Se só agregados estiverem autorizados, considerar contagens com proteção
  adequada ao risco de reidentificação; contagens exatas não são seguras por definição.
- **Posições reais:** num layout tipo PaCMAP/UMAP/força, a distância entre dois
  pontos pode aproximar relações do dataset, conforme a métrica e o método. As coordenadas reais podem permitir inferir
  ligações fortes; medir o efeito no layout e dataset concretos. Sem sessão, posições **esquemáticas** (por exemplo,
  espiral à volta do centro do grupo), função só do grupo e de uma ordem pública.
- **Ordem derivada do grafo:** se a ordem, o tamanho ou a escolha das entidades
  visíveis vêm de centralidade, grau ou "reach", revelam quem está mais ligado.
  Atributos públicos (por exemplo, capitalização bolsista) podem evitar
  divulgação direta, mas ainda se correlacionar com o grafo; avaliar o risco residual.
- **Vizinhos por entidade:** mesmo sem valores e por ordem alfabética, juntar os
  vizinhos de todas as entidades dá a lista de ligações. Prefere uma lista igual
  para todo o grupo (por exemplo, os líderes do grupo).
- **Composição completa por percurso:** se um detalhe responde para qualquer
  entidade, percorrer todas dá a composição de cada grupo. Responde só para as
  entidades que a vista pública já mostra.
- **Respostas de erro diferentes:** "escondida" versus "não existe" revela o
  universo e o nível. Devolve o mesmo status e corpo nos dois casos, a não ser
  que o universo já seja público.
- **Contornos e formas derivados das posições reais:** usa uma forma simples
  (círculo) sem sessão.
- **Histórico:** semanas anteriores e movimento permitem inferir estrutura ao
  longo do tempo. Decide por escalão, e recusa de forma uniforme ("histórico não
  disponível") sem dizer que semanas existem.

## O que cada escalão recebe é uma regra escrita e testada

- Regista a projeção no contrato de segurança mantido pelo produto (campos permitidos
  por rota, máximos, níveis, recusas), não como comentário no código.
- **Teste de extração autorizado:** usa fixtures locais ou ambiente isolado com
  rotas, contas, volume de pedidos e dados explicitamente autorizados. Não faças
  crawling exaustivo de produção nem introduzas uma fuga num serviço real como controlo.
  Reúne respostas no âmbito acordado, incluindo diferentes escalões e snapshots.
- Define critérios mensuráveis para esse atacante e cobertura: campos proibidos,
  reconstrução de ligações/pertenças acima de um limiar escolhido, e comparação
  com informação pública de base. Procurar pares de IDs e números inesperados é
  um sinal útil, não prova de confidencialidade ou de não reconstrução.
- **Controlo positivo:** só na fixture/ambiente isolado, introduz a fuga conhecida
  (posições reais, ordem derivada do grafo) e verifica que o exercício a deteta.
  Um controlo não detetado limita o valor do resultado negativo.
- Mede associação entre ordem visível e propriedades confidenciais contra uma
  referência adequada. Correlação pode vir de atributos públicos ou acaso; a sua
  ausência também não prova segurança. Documenta hipóteses, cobertura, resultados
  e ataques residuais, incluindo informação auxiliar e divulgação ao longo do tempo.

## Com sessão também é uma decisão

Uma conta gratuita é fácil de criar. Se "com sessão" recebe o dataset completo
numa só chamada, a barreira real é criar uma conta. Decide de forma explícita o
que o escalão gratuito recebe (por exemplo, o mapa real só da semana atual) e o
que fica para o escalão pago (histórico, movimento, pesos exatos).

## Orçamentos

Se o produto mede consultas de detalhe, decide se uma visão geral conta como uma
operação ou como várias: não debites cada entidade implicitamente. "Ticker
consultado" era a unidade do caso de origem, não uma unidade universal. Reutiliza
escalões e regras existentes quando existirem e forem adequados; caso contrário,
define-os com o produto. Se houver cache anónima, confirma limites e isolamento
por projeção: não reutilizes uma resposta privilegiada numa chave pública.

## Quando não aplicar

Dados que já são públicos na íntegra, ou vistas sem nenhum valor derivado de um
dataset proprietário. Uma correlação simples de preços públicos é reproduzível
por qualquer um; o que se protege é o que é vosso (fatores, residualização,
agrupamentos, universo curado).

## Relacionadas opcionais

As sugestões seguintes só acrescentam contexto se estiverem disponíveis; este
pacote inclui o método e os limites necessários ao seu âmbito.

- `enforceable-invariants-for-agent-code`: tornar a regra obrigatória por teste.
- `clerk-fastapi-trust-boundaries`: identidade e escalões.
- `guards-that-pass-blindly`: um teste de extração sem controlo pode passar às cegas.
