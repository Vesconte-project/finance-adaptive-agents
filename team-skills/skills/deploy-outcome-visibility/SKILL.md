---
name: deploy-outcome-visibility
description: Desenhar o sinal de saída de deploys, gates e trabalho automático para quem não está na máquina. Usa ao introduzir um gate que adia trabalho, ao escolher códigos de saída para estados novos, ao configurar alertas de falha, quando um CI fica vermelho por algo que funcionou como desenhado, ou quando alguém pergunta "como é que eu sei que isto entrou em produção?".
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

Um estado novo precisa de um código próprio **e** de tradução em cada fronteira.
Caso real, com um gate que adia a ativação quando há trabalho agendado nos 45
minutos seguintes:

| Camada | O que faz com o "adiado" | Se não for traduzido |
| --- | --- | --- |
| script validador | sai com 75 (código próprio, distinto de 1) | correto |
| unit systemd | sem `SuccessExitStatus=75`, marca a unit `failed` | primeiro degrau da mentira |
| cliente (`systemctl start`, `check=True`) | levanta exceção | segundo degrau |
| step de CI | fica **vermelho** | quem fez merge lê "o deploy falhou" |
| notificação | email de falha de CI | aprende-se a ignorar vermelhos |

A correção é uma linha na unit (`SuccessExitStatus=75`) **e** o cliente a
imprimir qual dos estados aconteceu. Nenhuma das duas sozinha resolve.

Depois de o exit 0 passar a significar "aceite", há uma dívida nova: **verde no
CI deixa de significar "em produção"**. Escreve isso no log do step, em letras,
e no README do repo. Senão as pessoas vão assumir o contrário, com razão.

## A assimetria que deixa o operador no escuro

O padrão mais comum: alerta-se a falha e não se sinaliza a conclusão.
Consequência exata — um deploy adiado que **entra** meia hora depois não produz
nenhum sinal. Quem fez merge ficou com um vermelho na cabeça e nunca soube que
resolveu.

Manda os dois sinais para o **mesmo** check de monitorização: falha e sucesso.
Assim ganhas três coisas:

- notificação nas **transições** (partiu / recuperou), sem ruído no meio;
- a cor do check reflete sempre o **último** resultado real;
- o histórico de eventos serve de registo de deploys, com diagnóstico no corpo.

## Dois tipos de check, configuração oposta

Confundir estes dois é fonte de alarmes falsos que treinam as pessoas a ignorar
o painel:

| Tipo | Alerta quando | Período | Exemplo |
| --- | --- | --- | --- |
| **Dead man's switch** | o ping **não** chega | curto (o do trabalho: diário, horário) | backup noturno, monitor periódico |
| **Alarme explícito** | alguém faz ping de falha | **o máximo possível** | falha de release, incidente pontual |

Um alarme explícito com período curto fica "down" sozinho por silêncio e
mente. Um dead man's switch com período infinito nunca deteta o silêncio, que
era o seu único propósito.

Dois detalhes que só se aprendem a usar:

- um check que nunca recebeu ping aparece **cinzento/"new"**, não verde. É
  facilmente confundido com "desativado". Diz isso na documentação.
- um alarme explícito **não se limpa sozinho**: fica vermelho até alguém enviar
  o sinal de recuperação. Documenta o comando de reset ao lado do de instalação.
  Sem ele, o painel acumula vermelhos antigos e perde-se o hábito de olhar.

## O corpo do ping é o diagnóstico

Quem recebe o alerta está fora da máquina; se a notificação só disser "falhou",
tem de abrir sessão — e voltaste ao início. Manda metadados suficientes para
decidir **se** é preciso agir:

- o que falhou (componente), em que versão (SHA completo), em que estado
  (vocabulário fechado de estados, não texto livre);
- a causa, truncada e higienizada: primeira linha, URLs e atribuições de
  segredo removidas, limite de caracteres;
- nunca tokens, DSNs ou valores de ambiente. A notificação atravessa email e
  serviços terceiros.

## Pedidos em sequência: o adiamento parcial

Armadilha real e caríssima. Um workflow pedia três componentes em sequência, no
mesmo bloco de shell com `-e`:

```
request-release COMPONENTE-A "$SHA"
request-release COMPONENTE-B "$SHA"
request-release COMPONENTE-C "$SHA"
```

Quando o gate adiou **A**, o shell abortou e **B e C nunca chegaram a ser
pedidos**. O retry automático só conhece A, porque só A tem pedido registado.
Meia hora depois: A na versão nova, B e C na antiga, nada a avisar, e um
vermelho no CI que parecia explicar tudo.

Regras:

- **escreve todos os pedidos antes de qualquer gate poder interromper**;
- a falha de um não impede os seguintes; reporta o estado agregado no fim;
- se houver retry, garante que cobre **todos** os pedidos registados;
- versões diferentes entre componentes do mesmo commit têm de ser detetáveis
  por uma sonda, não pela memória de ninguém.

## Testa o canal no dia em que o instalas

Um alerta que nunca disparou não é um alerta: é uma intenção. No dia da
instalação, envia um evento de teste pelo caminho real — o binário instalado, o
ficheiro de configuração real, o destino real — confirma que chega, lê o corpo,
e depois limpa. Custa dois minutos e é a diferença entre ter e achar que tens.

## Checklist antes de dar um gate por acabado

1. Cada estado tem código de saída próprio, distinto de 1?
2. Cada fronteira entre o script e o ecrã traduz esse código?
3. O sucesso depois de um adiamento produz sinal?
4. Um verde no CI diz explicitamente o que significa?
5. O alarme foi testado ponta a ponta e tem comando de reset documentado?
6. Um pedido múltiplo sobrevive a um adiamento no primeiro elemento?
7. Existe uma sonda de leitura que diga "o que está em produção agora", que
   qualquer pessoa consiga correr sem privilégios?

## Quando não aplicar

Se quem faz deploy é a mesma pessoa que administra a máquina e está lá sempre,
o custo disto não se paga — um `journalctl` resolve. O valor aparece no momento
em que existe **uma** pessoa, agente ou equipa que decide e não observa. Nesse
momento, aparece todo de uma vez.

## Relacionadas

- `orchestrator-runtime-ops`: quando e por que razão adiar em vez de interromper.
- `diagnose-host-failures`: secção "Sinais para fora da máquina", com estes casos
  indexados por sintoma.
- `verify-against-the-host`: a sonda que prova o que está mesmo em produção.
