---
name: deploy-outcome-visibility
description: Tornar visíveis os resultados aceite, concluído e falhado de um deploy ou gate de release a quem não acompanha o host. Usa ao desenhar esse fluxo de release; não para configurar alertas gerais nem diagnosticar falhas de CI sem relação com deploy.
---

# O operador não está no servidor

Quem faz merge não vai abrir sessão para confirmar. Não porque seja
descuidado — porque o trabalho dele acabou quando aprovou o PR. Toda a
informação que existe **só** no host é informação que ninguém vai ler.

Isto parece óbvio e falha-se sempre da mesma maneira: constrói-se um mecanismo
correto no servidor e esquece-se de o traduzir para fora. O mecanismo funciona,
e ninguém sabe.

## A regra

**Para cada estado que o sistema pode alcançar, escreve quem fica a saber e
por que caminho.** Se a resposta for "quem correr `systemctl status`", esse
estado é invisível. Um estado invisível é um estado que não existe para a
organização.

Faz a pergunta na forma mais dura: *se isto acontecer às 3 da manhã e ninguém
tiver sessão aberta, quem fica a saber, e como?*

## Três estados, não dois

Quase toda a tubagem de deploy sabe representar dois estados: **feito** e
**falhado**. No momento em que acrescentas um gate — uma janela de manutenção,
um lock, uma barreira de cobertura — crias um terceiro:

| Estado | Significa | Erro típico |
| --- | --- | --- |
| **aceite** | o pedido é válido e vai acontecer mais tarde | ser reportado como falha |
| **feito** | está em produção e verificado | ser inferido de um exit 0 que só significa "aceite" |
| **falhado** | não aconteceu e não vai acontecer sozinho | ser confundido com adiado, e ignorado |

O terceiro estado é o que parte tudo, porque **cada camada** entre o teu script
e o ecrã de quem fez merge tem de o saber traduzir. Basta uma não saber.

## Traça o código de saída por todas as camadas

Um estado novo precisa de uma representação distinta **e** de tradução em cada
fronteira do fluxo existente. Neste exemplo, um gate adia a ativação quando há
trabalho agendado nos 45 minutos seguintes:

| Camada | O que faz com o "adiado" | Se não for traduzido |
| --- | --- | --- |
| script validador | sai com 75 (código próprio, distinto de 1) | correto |
| unit systemd, se usada | sem `SuccessExitStatus=75`, pode marcar a unit `failed` | primeiro degrau da mentira |
| cliente, neste caso `systemctl start` com `check=True` | levanta exceção | segundo degrau |
| step de CI | depende de como traduz o resultado do cliente | quem fez merge pode ler "o deploy falhou" |
| notificação | email de falha de CI | aprende-se a ignorar vermelhos |

A configuração depende das semânticas do executor: numa unit systemd, confirma
o efeito de `SuccessExitStatus=75`; no cliente, confirma como esse código é
traduzido. Aplica essas opções apenas quando os componentes existem e o código
representa realmente "adiado" no sistema alvo.

Se a unit systemd tratar 75 como sucesso, `systemctl start` pode também devolver
sucesso. Isso só descreve o resultado da unit, não prova que o deploy foi
concluído; as camadas seguintes ainda têm de comunicar explicitamente "aceite".

Se exit 0 passar a significar "aceite", **verde no CI deixa de significar "em
produção"**. Documenta esse significado no artefacto de revisão aplicável e no
output do workflow, se existir.

## A assimetria que deixa o operador no escuro

O padrão mais comum: alerta-se a falha e não se sinaliza a conclusão.
Consequência exata — um deploy adiado que **entra** meia hora depois não produz
nenhum sinal. Quem fez merge ficou com um vermelho na cabeça e nunca soube que
resolveu.

Se o fornecedor suportar recuperação no mesmo check, considera enviar-lhe
falha e sucesso. Confirma primeiro as semânticas de transição e notificação; se
esse modelo não existir, escolhe um canal que distinga explicitamente falha de
recuperação. O modelo de mesmo check pode dar:

- notificação nas **transições** (partiu / recuperou), sem ruído no meio;
- a cor do check reflete sempre o **último** resultado real;
- o histórico de eventos serve de registo de deploys, com diagnóstico no corpo.

## Dois tipos de check, configuração oposta

Confundir estes dois é fonte de alarmes falsos que treinam as pessoas a ignorar
o painel:

| Tipo | Alerta quando | Período | Exemplo |
| --- | --- | --- | --- |
| **Dead man's switch** | o ping **não** chega | definido pela frequência esperada e tolerância ao atraso | backup noturno, monitor periódico |
| **Alarme explícito** | alguém faz ping de falha | configurado conforme o fornecedor, sem atraso ou supressão indesejados | falha de release, incidente pontual |

Estes períodos dependem do fornecedor e do tipo de check. Confirma no sistema
alvo como timeout, silêncio e recuperação são tratados; um período inadequado
pode criar alarmes falsos ou deixar de detetar silêncio.

Dois detalhes que só se aprendem a usar:

- em alguns fornecedores, um check sem pings aparece **cinzento/"new"**.
  Confirma e documenta o estado inicial real.
- alguns alarmes explícitos não se limpam sozinhos. Confirma como o sistema
  assinala recuperação e documenta o reset aplicável, se existir.

## O corpo do ping é o diagnóstico

Quem recebe o alerta está fora da máquina; se a notificação só disser "falhou",
tem de abrir sessão — e voltaste ao início. Manda metadados suficientes para
decidir **se** é preciso agir:

- o que falhou (componente), em que versão (SHA completo), em que estado
  (vocabulário fechado de estados, não texto livre);
- um código diagnóstico e campos de uma allowlist aprovada, sanitizados por um
  mecanismo testado; não encaminhes uma linha arbitrária de exceção/log apenas
  por remover URLs ou atribuições conhecidas;
- nunca tokens, DSNs, valores de ambiente ou texto livre não verificado.
  Respeita as regras de acesso e exposição de dados; se não houver sanitização
  confiável, omite a causa e envia apenas o código diagnóstico permitido.

## Pedidos em sequência: o adiamento parcial

Um workflow pode pedir vários componentes em sequência, por exemplo no mesmo
bloco de shell com `-e`:

```
request-release COMPONENTE-A "$SHA"
request-release COMPONENTE-B "$SHA"
request-release COMPONENTE-C "$SHA"
```

Num fluxo deste tipo, se o gate adiar **A** e o shell abortar, **B e C podem
nunca chegar a ser pedidos**. Um retry que só conhece A não cobre os pedidos
que não foram registados.

Antes de registar antecipadamente todos os pedidos, confirma que essa operação
é segura, idempotente e não inicia deploys antes de o gate os aceitar. Se for,
regista todos antes do gate. Caso contrário, usa uma transação ou outro
mecanismo que garanta que nenhuma parte do release começa isoladamente.

Se o workflow usar este padrão, considera também estas medidas:

- não deixes uma falha abortar pedidos independentes sem primeiro confirmar que
  continuar é seguro; reporta o estado agregado no fim;
- se houver retry, garante que cobre **todos** os pedidos registados;
- versões diferentes entre componentes do mesmo commit têm de ser detetáveis
  por uma sonda, não pela memória de ninguém.

## Testa o canal quando estiver autorizado

Um alerta que nunca disparou não foi validado ponta a ponta. Se as ferramentas,
o destino e a autorização estiverem disponíveis, testa pelo caminho que o
ambiente realmente usa. Prefere um canal de teste ou staging; não contactes
destinos reais, executes binários instalados nem faças resets de produção sem
autorização explícita. Sem essas condições, descreve o teste necessário sem o
executar.

## Checklist antes de dar um gate por acabado

1. Cada estado tem uma representação distinta e é traduzido em cada fronteira? Se o fluxo usar códigos de saída, cada estado relevante tem um código não ambíguo?
2. Cada fronteira entre o script e o ecrã traduz esse código?
3. O sucesso depois de um adiamento produz sinal?
4. Um verde no CI diz explicitamente o que significa?
5. O canal foi testado segundo as capacidades do fornecedor e a autorização disponível; o reset aplicável está documentado?
6. Um pedido múltiplo sobrevive a um adiamento no primeiro elemento?
7. Existe uma leitura do estado instalado adequada às funções autorizadas e às
  regras de acesso do ambiente? Se não puder ser disponibilizada, a limitação
  está documentada?

## Quando não aplicar

Se quem faz deploy é a mesma pessoa que administra a máquina e está lá sempre,
o custo disto não se paga — um `journalctl` resolve. O valor aparece no momento
em que existe **uma** pessoa, agente ou equipa que decide e não observa. Nesse
momento, aparece todo de uma vez.

Antes de afirmar que uma versão entrou em produção, verifica evidência adequada
ao alvo instalado (por exemplo, SHA ativo ou resultado de uma sonda autorizada).
Sem acesso ao host, declara essa limitação em vez de inferir o estado a partir
do CI.
