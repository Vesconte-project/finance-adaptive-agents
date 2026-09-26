---
name: host-mutation-batches
description: Planear um lote coordenado de alterações privilegiadas a vários componentes num host de produção, partilhando rollback definido e um passo de privilégio executado por um operador humano. Não para uma alteração de rotina isolada nem para trabalho apenas no repositório.
---

# Lotes em vez de mudanças soltas

Quando várias alterações relacionadas num host de produção exigem um passo
privilegiado do operador e partilham um rollback coerente, coordená-las pode
reduzir interrupções. Usa este modelo apenas se corresponder ao workflow e às
fronteiras de autorização do host; uma alteração isolada pode continuar a ser o
lote correto.

A regra é: **agrupar apenas mudanças relacionadas; não aumentar o risco para
reduzir pedidos**. O tamanho do lote depende das dependências, do rollback e da
janela autorizada.

## O contrato do script de lote

Se o workflow adotar um script de lote, um contrato possível tem quatro ações:

- **`stage`**: prepara a fonte imutável aprovada numa localização controlada e
  identifica-a por commit, digest de artefacto, versão assinada ou mecanismo
  equivalente. Verifica que o delta autorizado pertence a este lote e recusa
  alterações extra. Valida origem e integridade conforme o workflow; verifica
  refs/remotes Git apenas quando Git fizer parte dele.
- **`plan`**: só leitura, valida novamente o identificador da fonte e o âmbito
  autorizado do lote, corre o preflight completo, imprime o que vai mudar e **recusa** com
  mensagem clara se houver alterações extra ou outra pré-condição falhar.
- **`apply`**: usa confirmação explícita adequada à interface e autorização do
  operador, revalida a mesma fonte imutável e âmbito aprovado, processa
  componente a componente e regista o estado conforme o risco do workflow.
- **`rollback`**: repõe apenas alterações reversíveis cobertas por backups
  verificados. Credenciais já rodadas, deploys observados externamente e outras
  ações não reversíveis exigem um caminho de recuperação/forward-fix validado
  ou ficam fora do rollback automático, com esse limite explícito.

## Propriedades que valem cada linha

**Fonte verificada.** Quando o modelo de ameaça exigir isolamento da árvore de
trabalho, prepara a fonte num local controlado e verifica o commit exato, a
origem e a integridade. `git archive`, um caminho root-owned como
`/var/lib/...`, ou `python3 -I` são opções dependentes da plataforma e do
workflow, não requisitos universais. Nenhuma delas, isoladamente, prova que o
código é confiável.

**Preflight que recusa antes de tocar.** Verifica as pré-condições relevantes
para esse lote, como estado instalado, permissões, espaço e serviços, quando
esses recursos existirem e forem autorizados para inspeção. Se uma pré-condição
de segurança não puder ser verificada, não começa e explica o bloqueio.

**Janela de manutenção.** Se o host tiver trabalho agendado relevante, usa a
interface e a política do orquestrador real para detetar conflito e obter a
aprovação ou janela necessárias. Não assumes uma margem fixa nem um motor
específico.

**Estado retomável.** Cada componente concluído fica registado com evidência.
Correr outra vez continua de onde parou e revalida o que já estava feito. O
estado fica ligado ao identificador imutável da fonte aprovada; se esse
identificador mudar, recusa. Para Git, pode ser o commit exato.

**Rollback segundo a consistência aprovada.** Se os componentes forem
independentemente reversíveis e o estado parcial for seguro e autorizado, uma
falha no componente 3 pode reverter apenas esse componente e parar. Caso
contrário, segue a estratégia de rollback/recuperação do lote validada antes do
apply; não assumes que deixar 1 e 2 aplicados é seguro nem desfaz tudo às cegas.

**Backups antes de escrever.** Cada ficheiro tocado é copiado primeiro, com
marcador para os que não existiam. O `rollback` consome esses backups.

**Verificação que exercita o caminho real.** Quando for aplicável e autorizado,
confirma o resultado por um caminho observável adequado ao host e ao serviço.
Um pedido de deploy real, endpoint público ou execução agendada são exemplos,
não requisitos universais; usa um canal de teste quando disponível e não
provoques efeitos externos sem autorização.

## Ordem de trabalho com um humano

1. O agente prepara o trabalho e os testes sem executar operações privilegiadas.
2. O artefacto de revisão e a ordem dos passos seguem o workflow aprovado do
  repositório; PR, `stage` e `plan` só se existirem nesse workflow.
3. O operador executa cada passo que exige os seus privilégios, após rever o
  plano e confirmar o alvo.
4. O `apply`, se existir, ocorre apenas dentro da autorização e janela
  aprovadas.
5. O relatório indica as evidências obtidas e o que não foi verificado.

O workflow tem de executar `apply` apenas no ramo em que `plan` terminou com
sucesso. Usa uma condição explícita no chamador; não confies em `set -e`, cujo
comportamento depende do contexto do shell. Uma recusa de `plan` é uma proteção,
não um erro a contornar.

## Dimensionar um lote

Um lote pode incluir vários componentes quando partilham dependências, passo
privilegiado e rollback verificado. Não agrupes tudo por repositório; uma unit
ou um ficheiro pode ser o lote correto quando reduz o risco ou não partilha um
rollback seguro com outras mudanças.

## Template

Para desenhar o script, usa o contrato em
[references/batch-script-contract.md](references/batch-script-contract.md). O
script efetivo pertence ao repositório de infraestrutura do host e precisa de
testes contra os seus caminhos, identidades e serviços reais.

## Dois lotes que tocam no mesmo ficheiro

Uma armadilha possível não é evidente. Um lote declara o baseline do que espera
encontrar instalado, em hashes fixos. Se dois lotes mexerem no
**mesmo ficheiro instalado** e ambos forem integrados no ramo principal antes de
qualquer um ser aplicado, o primeiro a aplicar leva a fonte já com as alterações
do segundo — e o baseline do segundo passa a descrever um estado intermédio que
**nunca existiu**. O segundo recusa, corretamente, e não há nada para corrigir:
o resultado desejado já está instalado.

Antes de aplicar, confirma que a fonte imutável contém apenas alterações
autorizadas para esse lote. Se também contiver alterações de outro lote,
recusa-a ou usa uma fonte separada aprovada; nunca deixes a estratégia de
baseline autorizar alterações adicionais em silêncio. Quando Git fizer parte
do workflow, confirma o commit e o delta autorizados. Depois escolhe uma das
opções abaixo e regista-a no lote:

- não integrar o segundo antes de aplicar o primeiro (mais simples, exige
  disciplina de quem faz merge);
- declarar o baseline **relativo à fonte** em vez de um hash de um estado
  intermédio;
- aceitar que o baseline pode já ser o alvo — ver abaixo, mantendo a validação
  da fonte imutável e do âmbito autorizado.

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
