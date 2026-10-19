---
name: ci-cost-and-duration-under-agent-load
description: Reduzir trabalho repetido e medir jobs de CI pesados, repetidamente lentos ou muito variáveis, sobretudo com muitos pushes de agentes ou pressão na quota de minutos. Não para falhas funcionais de testes, medições isoladas de jobs baratos ou escolha de fornecedor de CI.
---

# Agentes multiplicam o CI

Agentes podem gerar muitos pushes: corrigem, reverificam, atualizam pins.
Se os triggers do repositório correrem CI completo em cada push a um PR aberto,
o trabalho repete-se. Uma prova de integração
pesada, multiplicada por agentes e repositórios, pode esgotar uma quota mensal
em dias. A decisão que esta Skill muda: **reduzir trabalho repetido e medir
antes de otimizar**, sem cortar as provas que protegem produção.

## Primeiro, não correr o que não é preciso

- **Adiar provas pesadas durante drafts é uma opção de política.** Confirma
  primeiro os checks obrigatórios, as regras de revisão e os triggers reais.
  Se a política o permitir, conserva os checks necessários em draft e adia só
  os jobs caros apropriados. Cobre a passagem a ready, novos pushes enquanto
  ready e reabertura; correr apenas em `ready_for_review` deixa esses casos
  sem validação. Cancelar ao voltar a draft também depende dessa política.
  No GitHub Actions, considera `opened`, `synchronize`, `reopened` e
  `ready_for_review`, com condições sobre o estado atual do PR; trata o evento
  `converted_to_draft` e a concorrência separadamente se quiseres cancelar.
  Os nomes são um exemplo desse fornecedor, não configuração pronta para outro.
- **Não uses filtros de caminhos para saltar provas críticas.** Poupar minutos
  saltando a prova que protege schema, deploy ou segredos troca custo por
  risco. Filtros de caminhos servem para jobs claramente independentes.
- Confirma a sintaxe atual dos eventos e condições na documentação do
  fornecedor; os nomes e o comportamento mudam.

## Medir antes de otimizar

Recolhe tempos por fase e trabalho executado. Se houver suporte e destino
apropriado, guarda um relatório legível por máquina como artefacto; caso
contrário, usa logs sanitizados ou uma medição local identificada. Regista o
que falta medir antes de atribuir o ganho a uma causa.

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
- compara CPU-segundos e tempo de relógio em trabalho equivalente, incluindo
  volume de dados, cache e retries. Mais CPU-segundos é compatível com CPU mais
  lento, mas também com mais trabalho ou outro caminho de execução; mais tempo
  de relógio sem aumento semelhante de CPU sugere espera. Confirma com métricas
  de I/O, rede e escalonamento antes de atribuir causalidade. Throttling de um
  contentor não mede por si toda a contenção do host;
- vigia a razão entre duração e timeout. Perto do limite, a variação normal
  passa a causar falhas sem erro nenhum.

## Alternativas com custo próprio

- **Merge queue:** pode reduzir atualizações manuais do ramo para testar a
  combinação com a base, mas não elimina automaticamente CI por push e pode
  acrescentar execuções de grupos. Confirma disponibilidade e custo. Em GitHub
  Actions, checks exigidos pela fila precisam também do evento `merge_group`.
- **Runner próprio:** muda a estrutura de custos, com infraestrutura e
  manutenção próprias; confirma a faturação aplicável. Isola o estado entre
  execuções, sobretudo quando corre código de PRs.

Preços e planos mudam: confirma-os no momento, com os números de uso reais.

## Quota esgotada a meio de uma operação

Observado a 19/10/2026: depois de dois dias com muitos PRs pequenos de correção,
cada um a correr a prova pesada completa (incluindo PRs só de documentação), o
budget do Actions esgotou durante uma janela de manutenção. O sintoma foi um
workflow que falha **antes de executar qualquer step**, sem mudança no workflow.
Confirma nas annotations do run e na faturação antes de procurar outra causa.

Uma quota esgotada não autoriza merge sem CI. Só prepara essa exceção se a
política existente do repositório a permitir e houver autorização explícita
para a alteração e exceção concretas. Não contornes branch protection, checks
obrigatórios ou gates de deploy; se impedirem o merge, deixa-o pendente.
Quando a exceção estiver autorizada:

- limita a exceção a uma alteração pequena, revista, com testes locais e a prova
  relevante corrida fora da CI;
- regista o SHA, a validação e as lacunas no tracker, se disponível e autorizado,
  ou no destino de revisão aprovado. Usa essa alteração como hipótese inicial
  de diagnóstico, sem assumir causalidade;
- corre a CI no ramo principal quando houver budget e confirma-a verde **antes**
  de qualquer passo que dependa dos seus artefactos (por exemplo, uma admissão
  que exige o recibo da prova desse manifesto).

Depois, mede onde foi o consumo (que jobs, em que PRs) antes de mudar o workflow.

## Quando não aplicar

Um repositório com CI barato, estável e pouco repetido não precisa deste
workflow. Justifica-se quando o custo, lentidão repetida, variabilidade ou
pressão na quota são concretos; a proporção de pushes feita por agentes, por
si só, não demonstra esse problema.

## Fontes e limites

[Eventos de GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
e [merge queues](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue),
consultados em 2026-10-19, sustentam o exemplo de eventos, não as medições históricas.
Os tempos e o incidente de quota acima são relatos do contexto de origem, sem
recibos incluídos neste pacote; não são previsões para outro repositório.

## Relacionadas

Se também estiverem disponíveis, `privilege-boundaries-ci-runner` aprofunda
privilégios de runners e `production-faithful-integration-proofs` aprofunda
fidelidade da prova. Este procedimento não depende desses pacotes.
