---
name: orchestrator-runtime-ops
description: Operar um orquestrador de trabalho agendado (Prefect, Airflow e semelhantes) que corre no mesmo host dos serviços: janelas de manutenção, pausar e repor agendamentos, provar que um worker trabalha mesmo, código clonado em tempo de execução, runs presas e variáveis de deployment. Usa antes de reiniciar um servidor de orquestração ou workers, ao migrar a identidade de um worker, ou quando um deploy pode apanhar trabalho a meio.
---

# Orquestradores: o que parte quando se mexe

Um orquestrador junta três coisas que normalmente estão separadas: um servidor
de API, workers de vida longa, e **definições de trabalho guardadas numa base
de dados**. A terceira é a que surpreende, porque não vive no repositório nem
no host.

## Antes de reiniciar seja o que for

**Pergunta se há trabalho a correr, e quando é o próximo.** Um restart mata os
processos filhos dos workers, e um flow interrompido a meio de escrever deixa
dados parciais — pior do que uma execução que simplesmente não aconteceu.

```bash
# runs ativas
curl -s -X POST $API/flow_runs/filter -H 'content-type: application/json' \
  -d '{"limit":10,"flow_runs":{"state":{"type":{"any_":["RUNNING","PENDING"]}}}}'

# próximos agendamentos
curl -s -X POST $API/flow_runs/filter -H 'content-type: application/json' \
  -d '{"limit":10,"sort":"EXPECTED_START_TIME_ASC","flow_runs":{"state":{"type":{"any_":["SCHEDULED"]}}}}'
```

Calcula as janelas livres a partir dos agendamentos **e da duração típica** de
cada trabalho: um job que começa às 23:10 e demora uma hora ocupa até às 00:15,
não até às 23:11. Exige margem (20 a 45 minutos) antes do próximo.

**Se precisares mesmo de uma janela e ela não existir**, pausar os agendamentos
é mais limpo do que deixar um job ser morto. Guarda a lista do que pausaste e
repõe-na no fim — uma execução diária saltada recupera-se; uma interrompida a
meio, não necessariamente.

## Provar que um worker trabalha

`is-active` não chega, e o estado `ONLINE` também não: o registo do worker
anterior, com o mesmo nome, sobrevive ao restart durante um tempo.

- Exige um **heartbeat posterior** ao instante em que a mudança começou.
- Melhor ainda: exige uma **execução real** terminada com sucesso. É a única
  prova de que o worker recebe trabalho, clona código e escreve onde deve.

## O código que corre pode não ser o que instalaste

Muitos orquestradores clonam o código no momento de cada execução, a partir de
um repositório e de um commit fixado nas definições de deployment. Nesse caso:

- a release instalada governa o **ambiente** (interpretador e dependências),
  não o código executado;
- se a publicação das definições não fizer parte da ativação, o symlink da
  release **mente** sobre o que corre;
- publicar as definições tem de ser verificado depois, comparando o commit
  fixado em cada deployment com o da release.

```bash
curl -s -X POST $API/deployments/filter -H 'content-type: application/json' -d '{"limit":200}' \
 | python3 -c "import json,sys,collections; print(collections.Counter((s['prefect.deployments.steps.git_clone']['repository'], s['prefect.deployments.steps.git_clone']['commit_sha'][:10]) for d in json.load(sys.stdin) for s in (d.get('pull_steps') or []) if 'prefect.deployments.steps.git_clone' in s))"
```

**Consequência ao mudar a identidade do worker:** o clone em tempo de execução
usa as credenciais da identidade nova. Aliases SSH, `known_hosts` e o `HOME` têm
de existir para ela, dentro do sandbox da unit. Verifica-o **dentro** do
contexto real (mesmo namespace, identidade e restrições), não de fora.

## As variáveis de deployment são uma camada de configuração — e de segredos

As definições guardam frequentemente variáveis de ambiente por deployment, que
se sobrepõem ao que a unit fornece. Duas consequências:

1. **Caminhos antigos sobrevivem lá dentro** e só rebentam quando a identidade
   ou as permissões mudam. Foi assim que 16 deployments continuaram a apontar
   para um diretório que a identidade nova não conseguia atravessar.
2. **Segredos acabam lá em texto simples.** Referências a cofres em ficheiros de
   configuração são resolvidas no momento da publicação, e o valor final fica
   guardado na base de dados do orquestrador, legível por quem alcance a API.

Regra: as variáveis de deployment devem conter apenas o que é específico
daquele trabalho e não é segredo. Credenciais e caminhos de máquina vêm do
ambiente da unit. Se encontrares um segredo ali, trata-o como exposto e roda-o.

## Adiar é melhor do que interromper — mas tem de se ver de fora

Quando uma mudança apanha trabalho a correr, adiar a ativação é mais seguro do
que matar o processo a meio. Mas um gate que adia cria um **terceiro estado** —
aceite, feito, falhado — e quase toda a tubagem a montante só sabe representar
dois. Consequências medidas num caso real: um adiamento legítimo apareceu como
CI vermelho, e o adiamento do primeiro de três pedidos impediu silenciosamente
os outros dois.

Antes de instalares o gate, mede também **quanto do dia ele fecha**: soma as
janelas de `agendamento − margem` até ao fim da execução típica. Numa pool com
15 execuções diárias e 45 minutos de margem, deu 9 horas fechadas em 24 (38%),
com o maior bloco contíguo de 1h30 — logo a expiração de 6 horas nunca dispara
por agendamento, só por uma run presa. Sem esta conta, não sabes se criaste um
gate ou um bloqueio.

A skill `deploy-outcome-visibility` trata o desenho do sinal.

## Runs presas

Um worker que morre sem transição de estado deixa runs eternamente em
`RUNNING`. Ocupam janelas de manutenção e podem consumir limites de
concorrência. Fecha-as por **ID exato**, depois de confirmar nome e hora, com
transição forçada para um estado terminal. Nunca em bloco por filtro.

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
