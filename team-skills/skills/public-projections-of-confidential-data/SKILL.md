---
name: public-projections-of-confidential-data
description: Desenhar ou rever a versão sem sessão (ou de um escalão inferior) de uma vista construída sobre um dataset agregado confidencial, como um mapa de relações, grafo, ranking, matriz de correlações ou embedding, quando o produto quer mostrar a forma sem permitir extrair os dados. Usa ao abrir rotas a anónimos, ao definir o que cada escalão recebe ou ao avaliar riscos de scraping. Não para controlo de acesso genérico nem para rate limiting isolado.
---

# A forma pode ser pública; os números por par não

Um produto quer muitas vezes mostrar uma vista "de montra" a quem não tem conta:
o mapa, as zonas, os nomes principais. O valor do produto está no dataset por
baixo. A pergunta não é **se** a vista é pública, mas **que campos** saem sem
sessão, e se a união de todas as respostas públicas reconstrói o dataset.

Evidência: desenho do atlas semanal de relações entre empresas, 18/10/2026
(cerca de 650 empresas, 25 zonas, ligações por correlação de retornos residuais).
A primeira proposta tinha fugas que não eram óbvias; o teste de extração com
controlo mostrou que a vista com posições reais deixava reconstruir mais de 60%
das ligações.

## Os limites por IP não protegem o dataset

Limites por IP e caches travam curiosos e custos, não quem quer extrair: trocar
de IP é barato. Se uma única resposta anónima traz o grafo inteiro com pesos, ou
se percorrer todas as entidades traz todas as ligações, os limites só atrasam.
Desenha a **projeção** primeiro; os limites são uma segunda camada.

## Fugas que não parecem fugas

- **Valores por par:** correlações, distâncias, pesos de ligação, mesmo
  arredondados. Sem sessão, entre grupos só saem contagens.
- **Posições reais:** num layout tipo PaCMAP/UMAP/força, a distância entre dois
  pontos aproxima a força da relação. As coordenadas reais reconstroem as
  ligações mais fortes. Sem sessão, posições **esquemáticas** (por exemplo,
  espiral à volta do centro do grupo), função só do grupo e de uma ordem pública.
- **Ordem derivada do grafo:** se a ordem, o tamanho ou a escolha das entidades
  visíveis vêm de centralidade, grau ou "reach", revelam quem está mais ligado.
  Usa só atributos públicos (por exemplo, capitalização bolsista).
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

- Escreve a projeção como regra de segurança no repositório (campos permitidos
  por rota, máximos, níveis, recusas), não como comentário no código.
- **Teste de extração:** como anónimo, percorre todas as rotas, níveis e
  entidades, junta tudo e prova que não há objetos com dois identificadores,
  nem números fora da lista permitida, e que nem a lista de ligações nem a
  composição completa dos grupos se reconstroem.
- **Controlo:** corre o mesmo ataque com a fuga presente (posições reais, ordem
  do grafo) e prova que o teste a apanha. Sem controlo, um teste que nunca falha
  não prova nada.
- Verifica estatisticamente que a ordem visível não está correlacionada com o
  grau no grafo acima do acaso.

## Com sessão também é uma decisão

Uma conta gratuita é fácil de criar. Se "com sessão" recebe o dataset completo
numa só chamada, a barreira real é criar uma conta. Decide de forma explícita o
que o escalão gratuito recebe (por exemplo, o mapa real só da semana atual) e o
que fica para o escalão pago (histórico, movimento, pesos exatos).

## Orçamentos

- Respostas de mapa ou visão geral não devem contar cada entidade mostrada como
  "ticker consultado"; senão o primeiro carregamento esgota o orçamento diário de
  um visitante. Conta só o detalhe pedido.
- Reutiliza os escalões e regras de extração existentes em vez de inventar
  números novos para a família nova; uma só política, uma só calibração.
- Confirma que a resposta pública cabe nos limites da cache anónima.

## Quando não aplicar

Dados que já são públicos na íntegra, ou vistas sem nenhum valor derivado de um
dataset proprietário. Uma correlação simples de preços públicos é reproduzível
por qualquer um; o que se protege é o que é vosso (fatores, residualização,
agrupamentos, universo curado).

## Relacionadas

- `enforceable-invariants-for-agent-code`: tornar a regra obrigatória por teste.
- `clerk-fastapi-trust-boundaries`: identidade e escalões.
- `guards-that-pass-blindly`: um teste de extração sem controlo pode passar às cegas.
