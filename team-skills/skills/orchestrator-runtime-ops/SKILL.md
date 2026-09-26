---
name: orchestrator-runtime-ops
description: Operar workers e deployments Prefect num host partilhado com serviços de produção, quando um restart, mudança de identidade ou deploy pode interromper trabalho agendado. Usa após confirmar que o ambiente é Prefect e que a versão/API corresponde; não para outros motores ou operação genérica de jobs.
---

# Orquestradores: o que parte quando se mexe

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

```bash
# Exemplo: primeira página; confirma endpoint/API e autenticação antes de usar.
curl -fsS -X POST "$API/flow_runs/filter" -H 'content-type: application/json' \
  -d '{"limit":10,"offset":0,"flow_runs":{"state":{"type":{"any_":["RUNNING","PENDING"]}}}}'

# Exemplo: primeira página de agendamentos; aplica o intervalo relevante.
curl -fsS -X POST "$API/flow_runs/filter" -H 'content-type: application/json' \
  -d '{"limit":10,"offset":0,"sort":"EXPECTED_START_TIME_ASC","flow_runs":{"state":{"type":{"any_":["SCHEDULED"]}}}}'
```

Cada comando mostra apenas uma página. Para decidir se é seguro reiniciar, usa a
paginação e o sinal de total/fim de página suportados pela versão confirmada até
cobrir todas as runs ativas e todos os agendamentos da janela relevante; não
interpretes 10 resultados como lista completa. Se a API não indicar completude,
declara a incerteza e não concluas que não há trabalho. `-f` e `-S` fazem erros
HTTP/transporte falharem visivelmente; uma falha não é uma resposta vazia. Atualiza
a consulta imediatamente antes do restart para reduzir corridas com novas runs.

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

- Exige um **heartbeat posterior** ao instante em que a mudança começou.
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

```bash
curl -fsS -X POST "$API/deployments/filter" -H 'content-type: application/json' -d '{"limit":200}' \
 | python3 -c "import json,sys,collections; print(collections.Counter((s['prefect.deployments.steps.git_clone']['repository'], s['prefect.deployments.steps.git_clone']['commit_sha'][:10]) for d in json.load(sys.stdin) for s in (d.get('pull_steps') or []) if 'prefect.deployments.steps.git_clone' in s))"
```

Este exemplo só se aplica à API Prefect confirmada, com endpoint configurado e
consulta autorizada; autentica pelo mecanismo seguro do cliente, sem tokens na
linha de comando. O limite de 200 é apenas uma página: pagina conforme o schema
da versão e confirma o total antes de tratar o resultado como inventário
completo. Um erro HTTP ou de transporte deve ser reportado, não contado como
lista vazia.

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

Servidor e workers são cliente e servidor da mesma API. Se vierem de locks
diferentes, divergem sem ninguém decidir. Define a versão de referência, fixa-a
nos dois lados e verifica publicação, heartbeat e uma execução real após
qualquer atualização.

## Quando não aplicar

Se o orquestrador corre noutra máquina, ou se o trabalho agendado é irrelevante
e idempotente, a maior parte disto não compensa. O peso justifica-se quando o
orquestrador partilha o host com os serviços e o trabalho escreve em dados que
te importam.
