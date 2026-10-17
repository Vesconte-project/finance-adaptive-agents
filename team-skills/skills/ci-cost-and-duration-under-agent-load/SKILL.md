---
name: ci-cost-and-duration-under-agent-load
description: Controlar o custo em minutos e a duração de CI quando agentes de código abrem muitos PRs e pushes, ou investigar um job de CI lento ou com tempos que variam entre execuções. Usa ao esgotar ou aproximar a quota de minutos, ao otimizar um job pesado, ou ao interpretar uma medição de tempo. Não para falhas de testes nem para escolher um fornecedor de CI.
---

# Agentes multiplicam o CI

Um agente faz mais pushes do que uma pessoa: corrige, reverifica, atualiza
pins. Cada push a um PR aberto corre o CI completo. Uma prova de integração
pesada, multiplicada por agentes e repositórios, pode esgotar uma quota mensal
em dias. A decisão que esta Skill muda: **reduzir trabalho repetido e medir
antes de otimizar**, sem cortar as provas que protegem produção.

## Primeiro, não correr o que não é preciso

- **Drafts não correm CI.** Dispara em `ready_for_review` e cancela execuções
  em curso quando um PR volta a draft. Os agentes trabalham em draft e só
  pedem revisão quando acabam.
- **Não uses filtros de caminhos para saltar provas críticas.** Poupar minutos
  saltando a prova que protege schema, deploy ou segredos troca custo por
  risco. Filtros de caminhos servem para jobs claramente independentes.
- Confirma a sintaxe atual dos eventos e condições na documentação do
  fornecedor; os nomes e o comportamento mudam.

## Medir antes de otimizar

Grava o tempo de cada fase num relatório legível por máquina, guardado como
artefacto de cada execução. Sem isso, qualquer otimização é palpite.

No caso que originou esta Skill, a intuição apontava para cache de imagens. As
medições mostraram que os builds custavam ~1 minuto, e que o maior ganho estava
em **trabalho repetido**: bases migradas duas vezes para comparações que podiam
usar as bases já criadas pela prova. Paralelizar fases independentes, cada uma
com o seu serviço efémero, deu o resto. O mesmo job passou de ~27 para ~18
minutos sem perder nenhuma verificação.

## Uma execução não é uma medição

Runners alojados com o mesmo rótulo (mesmos CPUs e RAM) podem ter
processadores de gerações diferentes. Observou-se o mesmo código a demorar 18
e 25 minutos. Por isso:

- decide com várias execuções e um critério escrito antes (por exemplo, "se
  as próximas 3 em main ficarem acima de X, ajusta");
- para distinguir **CPU mais lento** de **contenção**, compara os CPU-segundos
  gastos pelo mesmo trabalho: mais CPU-segundos para o mesmo trabalho aponta
  para processador mais lento; os mesmos CPU-segundos com mais tempo de relógio
  apontam para espera (contenção, disco, rede). Os contadores de throttling de
  um contentor só medem a quota desse contentor, não a contenção do host;
- vigia a razão entre duração e timeout. Perto do limite, a variação normal
  passa a causar falhas sem erro nenhum.

## Alternativas com custo próprio

- **Merge queue:** evita provas repetidas por cada push, mas os problemas entre
  PRs só aparecem mais tarde, e a disponibilidade depende do plano.
- **Runner próprio:** elimina o custo por minuto, mas traz manutenção e risco
  de estado persistente entre execuções, grave se o runner correr código de
  PRs.

Preços e planos mudam: confirma-os no momento, com os números de uso reais.

## Quando não aplicar

Um repositório com CI de poucos minutos e poucos pushes não precisa disto.
Justifica-se quando um job pesado domina o consumo, ou quando agentes geram a
maior parte dos pushes.

## Relacionadas

- `privilege-boundaries-ci-runner`: o que um runner pode ou não alcançar.
- `production-faithful-integration-proofs`: porque é que a prova pesada existe.
