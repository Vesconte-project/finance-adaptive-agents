---
name: agent-operating-agreement
description: Definir um acordo de trabalho para um agente que vai planear alterações autorizadas num servidor Linux de produção partilhado, incluindo revisão, verificações no host e reporte ao operador. Usa quando o utilizador pede explicitamente esse acordo; não para tarefas locais ou infraestrutura de desenvolvimento.
---

# Acordo de trabalho para um agente em produção

Estas práticas só se aplicam quando o utilizador e as instruções do repositório
adotarem este modo de trabalho, e apenas aos mecanismos existentes no ambiente.
Esta Skill não concede acesso, autorização ou capacidade para alterar o host.

## Lotes

O custo dominante é a ida e volta, não o trabalho. Cada pedido a um humano
custa-lhe contexto e tempo.

- Agrupa mudanças com o mesmo rollback num pedido de revisão. Inclui `merge`,
  `plan` ou `apply` apenas quando esses passos fazem parte do fluxo existente e
  foram autorizados; não combines aprovação e execução por defeito.
- Resolve descobertas dentro do âmbito aprovado e comunica cedo alterações
  materiais de risco, janela ou pressupostos.
- Só cria ou encadeia commits quando o utilizador autorizou essa ação e o fluxo
  aprovado do repositório a permite.
- Se o fluxo aprovado usar um script root para alterar o host, mantém nesse
  script as mudanças relacionadas do lote; não introduzas esse mecanismo se ele
  não existir.
- Lotes grandes nos **pedidos**, não no risco. O risco controla-se com
  preflight, verificação e rollback por componente.

## Antes de entregar

- Se o operador autorizou acesso ao host e as verificações são aplicáveis,
  executa-as em modo de leitura contra o alvo real. Caso contrário, identifica
  o que não foi verificado e fornece os passos para o operador.
- Se existir um workflow de CI aplicável, usa-o para validar o ambiente de
  execução relevante. Caso contrário, indica que essa validação não foi
  executada e porquê. Simula a ausência de contas Unix locais apenas quando os
  testes dependem delas.
- Parte do estado instalado quando o fluxo altera artefactos já instalados e
  esse estado pode ser inspecionado com autorização. Compara hashes quando o
  processo de instalação os usa como contrato.
- Quando existir uma interface de utilizador relevante e houver autorização,
  verifica o resultado por essa interface, não apenas pelo health interno.

## Reportar

- Resume o que muda, o pedido exato, a verificação posterior e riscos em aberto
  com o detalhe necessário para a decisão do operador.
- "Verificado" exige evidência: que comando, onde, que resultado.
- Não digas "os testes passaram" sem dizer em que ambiente.
- Se um risco ficou aceite, diz qual e porquê, sem o esconder na lista.

## Decidir

- Com default sensato: decide e documenta a assunção no artefacto de revisão
  aplicável, se o fluxo do repositório o prever, e continua.
- Sem default: pergunta, mas só nas que são irreversíveis, de política, ou que
  mudam a forma de trabalhar do humano (credenciais, grupos, acessos).
- Quando uma regra local do repositório te bloquear, pára e reporta em vez de
  contornar em silêncio.

## O que nunca fazer

- Correr como root código que vive num diretório onde outro utilizador escreve.
- Copiar credenciais para outra identidade sem confirmar o que essa credencial
  permite.
- Pedir uma password de sudo, ou pedir que a proteção seja desligada
  "temporariamente".
- Apagar dados, artefactos ou releases sem inventário e confirmação explícita.
- Corrigir à mão no host algo que o script do lote vai verificar por hash: cria
  drift e faz falhar o lote seguinte.

## Rever trabalho de outro agente

Para alterações ao host, revê o delta face ao estado instalado, a identidade
que executa cada passo, o efeito noutros serviços, o rollback e as verificações.
Só executa sondas no host se a plataforma corresponder, o operador autorizar o
acesso e a sonda não ultrapassar o âmbito aprovado; caso contrário, documenta
o comando e deixa a execução para o operador.
