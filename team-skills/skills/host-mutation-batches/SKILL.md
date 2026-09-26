---
name: host-mutation-batches
description: Planear e executar alterações num servidor de produção por lotes, com um único script root que tem plan, apply e rollback, preflight que recusa, estado retomável e evidência no fim. Usa quando um agente precisa de mudar units, permissões, identidades, credenciais ou deploys num host, e cada alteração exige a intervenção de um humano com sudo.
---

# Lotes em vez de mudanças soltas

Num servidor onde só um humano tem `sudo`, o custo dominante não é o trabalho:
é a ida e volta. Uma alteração por PR, com merge e `sudo` de cada vez, esgota
a paciência e o orçamento antes de o trabalho estar feito.

A regra é simples: **lotes grandes nos pedidos, não no risco**. O risco
controla-se com preflight, verificação e rollback por componente, não com mais
interrupções.

## O contrato do script de lote

Um único executável, com quatro ações:

- **`stage`**: exporta o commit revisto para uma cópia root-owned e verifica
  que a árvore está limpa e que o `HEAD` é o `main` remoto.
- **`plan`**: só leitura, corre o preflight completo, imprime o que vai mudar,
  e **recusa** com mensagem clara se alguma pré-condição falhar.
- **`apply`**: exige confirmação literal (`APPLY:nome-do-lote`), processa
  componente a componente e grava estado ao longo do caminho.
- **`rollback`**: repõe o que o lote mudou, a partir dos backups que ele
  próprio fez.

## Propriedades que valem cada linha

**Fonte verificada.** O `apply` nunca instala a partir de um diretório onde
o utilizador escreve. O `stage` faz `git archive` do commit exato para
`/var/lib/.../source/<sha>`, root-owned, e o `apply` recusa correr de outro
sítio. Usa `python3 -I` para o diretório do script não entrar no `sys.path`.

**Preflight que recusa antes de tocar.** Verifica hashes do que está
instalado, modos e donos dos ficheiros de segredos, espaço em disco, estado
dos serviços, e o que mais o lote assume. Se alguma coisa não bate certo,
não começa.

**Janela de manutenção.** Se o sistema tem trabalho agendado, o preflight
recusa quando há execuções em curso e exige margem (por exemplo 20 minutos)
antes da próxima. Mostra as próximas, para o humano escolher a hora.

**Estado retomável.** Cada componente concluído fica registado com evidência.
Correr outra vez continua de onde parou e revalida o que já estava feito. O
estado fica ligado ao commit da fonte: se o commit mudar, recusa.

**Rollback por componente.** Uma falha no componente 3 desfaz o componente 3,
deixa 1 e 2 no estado verificado, e pára. Nunca desfaz tudo às cegas.

**Backups antes de escrever.** Cada ficheiro tocado é copiado primeiro, com
marcador para os que não existiam. O `rollback` consome esses backups.

**Verificação que exercita o caminho real.** Não basta confirmar que o
ficheiro ficou instalado. Tem de correr o que o utilizador usa: um pedido
real pelo canal de deploy, um endpoint público, uma execução do serviço
agendado. Ver a skill `verify-against-the-host`.

## Ordem de trabalho com um humano

1. O agente prepara o lote inteiro: código, testes, docs, sem `sudo`.
2. Entrega **um** pedido: PR para merge + `stage` + `plan`.
3. O humano corre `stage` e `plan` e cola o resultado.
4. Só depois corre o `apply`, dentro da janela.
5. O agente volta com o resumo e a evidência, não com "verificado".

Se o `plan` recusar, o `set -e` do bloco impede o `apply`. Essa recusa é uma
funcionalidade, não um erro.

## Dimensionar um lote

Um lote deve ser o maior conjunto que partilha um rollback coerente. Bons
cortes: "todos os componentes deste repositório", "as identidades e o runner",
"o motor e a reconciliação das units". Maus cortes: "uma unit", "um ficheiro".

## Template

Para desenhar o script, usa o contrato em
[references/batch-script-contract.md](references/batch-script-contract.md). O
script efetivo pertence ao repositório de infraestrutura do host e precisa de
testes contra os seus caminhos, identidades e serviços reais.

## Dois lotes que tocam no mesmo ficheiro

A armadilha custou-me uma tarde e não é evidente. Um lote declara o baseline do
que espera encontrar instalado, em hashes fixos. Se dois lotes mexerem no
**mesmo ficheiro instalado** e ambos forem integrados no ramo principal antes de
qualquer um ser aplicado, o primeiro a aplicar leva a fonte já com as alterações
do segundo — e o baseline do segundo passa a descrever um estado intermédio que
**nunca existiu**. O segundo recusa, corretamente, e não há nada para corrigir:
o resultado desejado já está instalado.

Escolhe uma das três, e escreve-a no documento do lote:

- não integrar o segundo antes de aplicar o primeiro (mais simples, exige
  disciplina de quem faz merge);
- declarar o baseline **relativo à fonte** em vez de um hash de um estado
  intermédio;
- aceitar que o baseline pode já ser o alvo — ver abaixo.

## "Já está como queríamos" não é drift

Um lote tem de distinguir três situações que se parecem: o instalado é o que
esperava (aplica), o instalado é **já o alvo** (registar `APPLIED` como no-op,
com a razão, sem instalar nem arquivar nada), e o instalado é outra coisa
qualquer (recusar). Sem o caso do meio, a única saída é intervenção manual —
que é precisamente o que o lote existe para evitar.

Do mesmo lado: um receipt de uma tentativa **falhada e revertida** não pode
trancar a repetição. Aceita seguir a partir de `ROLLED_BACK` e
`FAILED_ROLLED_BACK`, incrementa um contador de tentativa, e antes de reutilizar
um backup retido **valida-o contra os hashes de baseline** e arquiva-o. Um
backup deteriorado deve fazer o lote recusar, não restaurar lixo.

## Quando reduzir o rigor

Se a máquina é descartável, ou se o humano tem sudo sem fricção e está a
acompanhar, o essencial reduz-se a três coisas: preflight que recusa, backup
antes de escrever, e um rollback testado. O resto (fonte root-owned, estado
retomável, receipts) só compensa quando as mudanças são muitas e
espaçadas no tempo.
