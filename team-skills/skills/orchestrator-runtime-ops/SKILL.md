---
name: orchestrator-runtime-ops
description: Operar workers e deployments Prefect num host partilhado com serviços de produção, quando um restart, mudança de identidade ou deploy pode interromper trabalho agendado. Usa após confirmar que o ambiente é Prefect e que a versão/API corresponde; não para outros motores ou operação genérica de jobs.
---

# Prefect no host partilhado: o que parte quando se mexe

Esta skill trata de ambientes Prefect. Os exemplos pressupõem uma API e um
modelo de deployments compatíveis com a versão em que foram escritos; confirma
as versões instaladas do servidor e cliente, a configuração real e o schema/API
suportado antes de usar endpoints ou inferir semânticas. Não assumes que outro
orquestrador partilha o mesmo modelo de API, workers ou definições persistidas.

## Antes de reiniciar um worker Prefect

Antes de qualquer operação, confirma que o alvo é Prefect, a versão/API,
workspace, identidade, permissões de leitura/alteração e aprovação necessária.
Confirma também qual serviço será reiniciado e se o operador autorizou a janela.
Não pauses schedules nem reinicies serviços automaticamente.

**Pergunta se há trabalho a correr, e quando é o próximo.** Um restart pode
interromper processos filhos; um flow interrompido durante uma escrita pode
deixar dados parciais. Usa apenas consultas compatíveis com a API confirmada e
com acesso autorizado, pedindo apenas os campos necessários e removendo
segredos dos resultados apresentados.

Não há aqui um JSON de filtro universal: consulta o OpenAPI/schema do servidor
ou os modelos/métodos do cliente **instalado** antes de construir a consulta.
Regista os seguintes critérios e valida que o pedido realmente os aplica:

- âmbito: pools, queues, deployments e instâncias potencialmente afetados;
- estados com processos, submissão ou efeitos ainda possíveis, incluindo
  transições/cancelamentos relevantes para essa versão. `RUNNING` e `PENDING`
  sozinhos não demonstram ausência de trabalho em risco; cruza com processos
  e serviço quando o estado da API não seja suficiente;
- janela de agendamentos: limites inferior e superior explícitos, timezone e
  campo temporal suportado. Confirma na resposta que o filtro cobre a janela
  pretendida, incluindo runs atrasadas e retries conforme o modelo instalado;
- paginação, ordenação e sinal de completude da versão confirmada. Uma página
  vazia ou dez resultados não bastam quando filtros/total não foram verificados.

Autentica pelo mecanismo seguro já configurado do cliente, sem tokens na linha
de comando. Evita imprimir respostas completas: a recolha autorizada pode
conter parâmetros e job variables secretos. Projeta apenas IDs necessários,
estado e instantes relevantes depois de validar a forma da resposta; nomes e
mensagens livres também precisam de sanitização. Não uses `curl -v`, tracing ou
ficheiros de resposta desprotegidos para investigar credenciais.

Falha HTTP, transporte, parsing ou cobertura incompleta é uma verificação
falhada, não ausência de runs. Em pipelines shell usa `set -o pipefail` e
confirma cada estado de saída; mantém a resposta original fora dos logs.
Atualiza a consulta imediatamente antes do restart e considera a corrida com
novas submissões: só uma política/gate apropriado pode controlar essa janela.

Calcula janelas livres com os agendamentos e duração observada dos trabalhos.
Acrescenta uma margem apenas conforme a política e variabilidade desse
ambiente; os exemplos de horários ou margens não são limiares universais.

Se uma janela autorizada não existir e a política permitir pausar trabalho,
guarda o estado exato dos schedules afetados e a aprovação do operador antes de
pausar. Restaura apenas os schedules alterados por esta operação e confirma o
estado final; considera execuções perdidas e efeitos de negócio antes de decidir
se uma run pode ser retomada.

## Provar que um worker trabalha

`is-active` não prova que o worker Prefect está a receber trabalho. O estado e
a persistência de registos `ONLINE` dependem da versão e configuração; confirma
o comportamento real antes de os usar como evidência.

- Liga o heartbeat à **nova instância e release**: PID com start time,
  invocation do serviço e identificador único do worker quando disponíveis.
  Exige heartbeat dessa instância depois de arrancar; só nome reutilizado e
  timestamp posterior não excluem o processo antigo ou outro concorrente.
  Se faltar identidade única, corrobora logs da nova invocation e release,
  demonstrando que as instâncias anteriores/concorrentes não emitem com o
  mesmo nome. Sem essa ligação, readiness fica não verificada.
- Uma execução terminada com sucesso pode testar um caminho adicional apenas
  se houver autorização explícita e um canary seguro, idempotente e sem efeitos
  externos indesejados. O sucesso valida só o caminho exercitado; não prova que
  todos os workers, clones, ações ou destinos de escrita estão corretos. Se não
  houver canary aprovado, usa evidência não mutante e declara a limitação.

## O código que corre pode não ser o que instalaste

Quando a configuração Prefect efetivamente clona código no momento da execução
a partir de um commit fixado no deployment (confirma versão e pull steps),
então compara os commits configurados com a release.

- a release instalada governa o **ambiente** (interpretador e dependências),
  não o código executado;
- se a publicação das definições não fizer parte da ativação, o symlink da
  release **mente** sobre o que corre;
- publicar as definições tem de ser verificado depois, comparando o commit
  fixado em cada deployment com o da release.

Para inspecionar uma recolha JSON já autorizada, lê
[references/safe-deployment-inventory.md](references/safe-deployment-inventory.md).
O exemplo valida a forma antes de imprimir uma projeção sem URLs e representa
a ausência de commit fixado como achado. Não recolhe dados nem certifica que o
servidor executará o commit: confirma a implementação do pull step instalada,
pagina com completude verificada e compara com o código efetivamente resolvido.
Um erro não pode virar um inventário vazio.

**Consequência ao mudar a identidade do worker:** se a configuração clonar em
runtime, confirma os aliases SSH, `known_hosts` e `HOME` efetivos da identidade
nova sem revelar chaves ou valores secretos. Usa apenas ferramentas e
permissões autorizadas, dentro do contexto real quando namespace e restrições
forem relevantes.

## As variáveis de deployment são uma camada de configuração — e de segredos

Na versão e configuração Prefect que suporta variáveis por deployment, confirma
se são aplicadas e como interagem com o ambiente do worker; não assumes
precedência universal. Inspeciona apenas com acesso autorizado e não imprimas
valores de credenciais. A persistência de valores de vault/secret depende da
versão e do fluxo de publicação; confirma onde são resolvidos e guardados antes
de concluir que foram expostos. Possíveis consequências incluem:

1. **Caminhos antigos sobrevivem lá dentro** e só rebentam quando a identidade
  ou as permissões mudam. Num exemplo de incidente, deployments continuaram a
  apontar para um diretório que a identidade nova não conseguia atravessar.
2. **Segredos podem acabar lá em texto simples.** Em algumas configurações,
  referências a cofres podem ser resolvidas durante a publicação e o valor
  final persistido no backend; verifica a versão, o fluxo e as permissões
  efetivos antes de tirar essa conclusão.

Revisa variáveis de deployment segundo a política do ambiente. Se um valor
secreto tiver sido exposto a uma API ou utilizadores não autorizados, segue o
procedimento de incidente e rotação de credenciais aprovado; não rodes credenciais
nem publiques definições sem autorização e plano de recuperação.

## Adiar é melhor do que interromper — mas tem de se ver de fora

Quando uma mudança apanha trabalho a correr, adiar a ativação é mais seguro do
que matar o processo a meio. Mas um gate que adia cria um **terceiro estado** —
aceite, feito, falhado — e quase toda a tubagem a montante só sabe representar
dois. Num exemplo de fluxo, um adiamento apareceu como CI vermelho e
interrompeu pedidos seguintes. Trata-se de um caso, não de comportamento
esperado em todos os sistemas.

Se o gate e a política de janela forem usados, estima o impacto com os
agendamentos, duração e margem medidos para esse ambiente. Os números de um
exemplo não são metas nem limites de timeout; documenta as hipóteses e valida a
política com o operador antes de instalar o gate.

Define no próprio workflow como os estados aceite, concluído e falhado chegam
ao operador; não infiras conclusão a partir de um resultado de CI verde.

## Runs presas

Uma run que parece presa pode ainda ter um processo ativo ou efeitos em curso.
Antes de qualquer transição terminal, confirma o backend/versão, identifica o
run exato, verifica o worker e resolve ou pára com segurança o processo
subjacente; avalia efeitos parciais e possibilidade de recuperação. Só depois,
com autorização explícita e pela API suportada, considera uma transição forçada
para o ID exato. Uma alteração de estado na API não prova que o trabalho parou;
nunca atualizes runs em bloco por filtro.

## Versões entre servidor e workers

Compara as versões e locks do servidor e workers com a matriz de compatibilidade
da instalação; versões diferentes não provam incompatibilidade por si só.
Define a referência suportada antes de propor alterações. Só fixa/altera versões
ou publica definições com autorização para essa mudança, reutilizando a que já
cobrir o âmbito, e com recuperação planeada. Depois de uma atualização autorizada,
verifica publicação e heartbeat da nova instância/release. Uma execução real
segue exatamente a regra de canary aprovado, seguro e idempotente de “Provar que
um worker trabalha”; sem esse canary, usa evidência não mutante e declara a
limitação. Um pedido de diagnóstico não autoriza upgrade nem execução de flows.

## Quando não aplicar

Se o orquestrador corre noutra máquina, ou se o trabalho agendado é irrelevante
e idempotente, a maior parte disto não compensa. O peso justifica-se quando o
orquestrador partilha o host com os serviços e o trabalho escreve em dados que
te importam.

## Fontes de implementação

Consultadas em 20/10/2026: [pull steps Prefect](https://reference.prefect.io/prefect/deployments/steps/pull/)
[armazenamento de código](https://docs.prefect.io/v3/how-to-guides/deployments/store-flow-code),
[filtros de runs](https://reference.prefect.io/prefect/server/schemas/filters/) e
[cliente de orquestração](https://reference.prefect.io/prefect/client/orchestration/).
Documentação online não estabelece o schema ou assinatura da instalação alvo.
