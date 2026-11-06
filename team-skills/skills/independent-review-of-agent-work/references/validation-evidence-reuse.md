# Rever cedo e reutilizar evidência válida

Usa quando uma entrega já tem ciclos repetidos de correção, CI pesado ou provas
duplicadas entre autor e revisor. O objetivo é encontrar falhas antes das execuções
caras, sem retirar checks obrigatórios ou fingir que resultados antigos provam
código novo. Esta referência não altera a política de CI do repositório.

## Ordem útil quando a política permite

- Prepara cedo a combinação de alterações que partilham o mesmo percurso. PRs
  separados podem continuar separados, mas os resultados isolados não comprovam
  uma combinação ainda não testada.
- Revê o diff e as passagens produtor → artefacto → consumidor → decisão antes
  de pedir outra execução integral. Procura onde se perdem linhas, campos ou
  causas. Usa a saída real do produtor no teste do consumidor; reconstruir o
  objeto intermédio pode esconder o defeito.
- Reproduz o risco com uma seleção dirigida e compara com a base exata. Uma
  correção repete primeiro o contraexemplo e os vizinhos afetados. Alarga quando
  o alcance da mudança ou uma dúvida concreta o justificar.
- Depois da revisão dirigida, fixa o candidato e verifica a validação completa
  exigida nesse SHA e combinação. Se a política já obriga a execuções anteriores,
  conserva-as; não desligues triggers ou checks para impor esta ordem.

O revisor mantém independência ao escolher contraexemplos e verificar evidência,
não por executar necessariamente uma segunda cópia de todas as suites do autor.
Uma reprodução independente dirigida é útil mesmo com CI verde.

## O recibo necessário para reutilizar uma prova

Confirma código e baseline exatos, seleção/comando, fixtures, ambiente relevante
(dependências, imagem, identidade e serviços) e resultado, incluindo falhas/skips e
limitações. No CI, verifica run, tentativa, SHA e jobs efetivamente executados.
Uma indicação verde ou uma contagem de testes isolada não identifica a prova.

Reutiliza a baseline quando esses elementos relevantes não mudaram e o recibo
está disponível e íntegro. Regista que a prova foi reutilizada, não repetida.
Resultados completos do CI no mesmo objeto podem ser verificados pelo revisor;
mantém as reproduções locais exigidas pela política e as que esclarecem riscos
específicos. Um job skipped não passa a aprovado por existir outro run verde.

## Quando é preciso repetir

- Mudou código relevante, fixtures, dependências, configuração ou o ambiente
  necessário à conclusão.
- Mudou a combinação com main, ou uma resolução de conflito alterou o percurso.
- Uma falha, incerteza ou hipótese nova exige uma prova diferente.
- Um check obrigatório exige execução naquele objeto/evento/contexto.

Não declares um SHA novo integralmente validado com resultados de outro SHA.
Eventual reutilização entre versões precisa de um mecanismo de equivalência
previsto pela política; não a inventes por o diff parecer pequeno.

Antes de repetir uma prova cara, explicita o que mudou, que dúvida nova será
resolvida ou que requisito exige o run. Sem isso, verifica o recibo existente.
Isto reduz duplicação; não garante que a primeira revisão encontre todos os
defeitos nem elimina a necessidade de nova prova quando surge um contraexemplo.

Origem: iterações de revisão em 2026-11 com suites verdes e lacunas nas passagens
entre componentes. A estratégia é uma melhoria proposta a partir desse caso;
não há medição de poupança ou garantia de eficácia noutros projetos neste pacote.
