---
name: agent-operating-agreement
description: Como um agente deve trabalhar num servidor de produção partilhado com humanos: tamanho dos lotes, o que verificar antes de pedir alguma coisa, o que reportar e o que decidir sozinho. Usa ao iniciar um agente em trabalho de infraestrutura, ao definir o modo de trabalho, ou quando o ciclo de idas e voltas está a consumir demasiado tempo.
---

# Acordo de trabalho para um agente em produção

Práticas aprendidas numa migração de produção com revisão humana. Aplica-as
quando o utilizador e as instruções do repositório adotarem este modo de
trabalho; esta Skill não concede acesso nem substitui essas instruções.

## Lotes

O custo dominante é a ida e volta, não o trabalho. Cada pedido a um humano
custa-lhe contexto e tempo.

- Agrupa mudanças com o mesmo rollback num pedido de revisão: merge + `plan` +
  `apply`, quando o utilizador autorizou a execução.
- Resolve descobertas dentro do âmbito aprovado e comunica cedo alterações
  materiais de risco, janela ou pressupostos.
- Podes encadear commits no mesmo branch antes do merge.
- Todas as mudanças no host de um lote vão num único script root.
- Lotes grandes nos **pedidos**, não no risco. O risco controla-se com
  preflight, verificação e rollback por componente.

## Antes de entregar

- Corre **todas** as verificações que o `apply` fará, em modo leitura, contra o
  host real. Uma verificação que nunca correu contra a máquina não está
  testada, e foi assim que três `apply` falharam seguidos.
- Corre a suite no ambiente do CI, não só no host. Se os testes dependem de
  contas Unix locais, simula a ausência delas.
- Parte do estado **instalado**, nunca do ficheiro do repositório. Compara
  hashes antes de escrever uma unit nova.
- Verifica o que o utilizador usa, não só o health interno.

## Reportar

- Resume o que muda, o pedido exato, a verificação posterior e riscos em aberto
  com o detalhe necessário para a decisão do operador.
- "Verificado" exige evidência: que comando, onde, que resultado.
- Não digas "os testes passaram" sem dizer em que ambiente.
- Se um risco ficou aceite, diz qual e porquê, sem o esconder na lista.

## Decidir

- Com default sensato: decide, regista como assunção no PR, e continua.
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

Trabalha pela mesma ordem: o que muda no host, quem corre o quê, o efeito nos
outros serviços, o rollback, as verificações, e só no fim o código. Reproduz
as suspeitas com sondas em vez de opinar. Ver `verify-against-the-host`.

## Quando relaxar

Num protótipo ou numa máquina descartável, mantém três coisas e larga o resto:
preflight que recusa, backup antes de escrever, e rollback testado.
