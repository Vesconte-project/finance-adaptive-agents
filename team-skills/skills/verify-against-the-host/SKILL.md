---
name: verify-against-the-host
description: Rever uma alteração destinada a modificar um host de produção — como uma unit, deploy ou script privilegiado — comparando as suposições da proposta com o estado instalado. Usa apenas para mudanças que atuam no host; não para revisão genérica de código só porque os testes passaram.
---

# Verificar contra o host, não contra o repositório

A maior parte dos erros que chegam a produção não vêm de desenho fraco. Vêm de
o autor ter escrito a partir do repositório enquanto a máquina tinha outra
coisa instalada.

## Regra

Antes de recomendar uma alteração ao host, compara as suposições da proposta
com evidência adequada. Sondas à máquina só se executam com autorização
explícita, acesso apropriado e dentro do âmbito aprovado. Sem essas condições,
revê os artefactos fornecidos, indica o que não foi possível verificar e não
exijas acesso como pré-condição para ajudar.

## Exemplos de verificação

Confirma primeiro sistema operativo, runtime, caminhos, unidades, nomes de
remotos e ferramentas disponíveis. Os exemplos abaixo só se aplicam quando
essas premissas forem verdadeiras. Classifica cada comando quanto a acesso,
contacto remoto, possível exposição de dados e efeitos antes de o executar.

**Drift entre a proposta e o instalado.** Não assumes que o repositório
representa o estado atual. Se host, runtime e caminhos forem confirmados, usa o
commit exato que contém a revisão proposta. Se esse objeto não existir no clone
local, obtém-no do remote/ref confirmado apenas se o contacto remoto estiver
autorizado; não substituas a revisão por `origin/main` nem por um branch móvel.

```bash
set -o pipefail
if ! git -C "$REPO" cat-file -e "$REVIEWED_SHA:$UNIT_FILE"; then
  printf '%s\n' 'Não foi possível resolver o ficheiro no commit revisto.' >&2
  exit 1
fi
git -C "$REPO" show "$REVIEWED_SHA:$UNIT_FILE" | sha256sum || exit 1
sha256sum "$INSTALLED_UNIT_FILE" || exit 1
```

`REVIEWED_SHA`, ficheiro e caminho instalado são valores confirmados para esta
revisão e host. Uma falha em qualquer comando torna a comparação inconclusiva;
nunca a trates como igualdade.

**Ambiente de um processo Linux**, apenas com autorização e PID de um serviço
systemd confirmado:

```bash
pid=$(systemctl show UNIT -p MainPID --value)
tr '\0' '\n' < /proc/$pid/environ | cut -d= -f1
```

O exemplo imprime apenas nomes do ambiente inicial exposto em `/proc`, não
valores, fontes ou necessariamente a configuração efetivamente consumida pela
aplicação. Um `.env` no repositório também não prova o que está instalado.

**Dependências entre units systemd**, quando o host usa systemd e a inspeção
está autorizada:

```bash
systemctl list-dependencies --reverse --plain UNIT
```

Confirma a semântica na versão instalada; não pares nem reinicies units apenas
com base nesta listagem.

**Sonda contextual de restrições de sandbox**, apenas se `setpriv`, sudo e a
configuração correspondente existirem e a execução estiver autorizada:

```bash
setpriv --no-new-privs sudo -n -l
```

O resultado depende da configuração e do contexto efetivos; não prova por si só
que todas as operações sudo ou todas as units se comportem da mesma forma.

**Reproduzir o ambiente de CI** apenas quando a proposta executa código no host
ou depende de contas Unix locais e o repositório fornece esse teste. Adapta as
contas e o runner às definições verificadas; este exemplo não é requisito geral:

```bash
PYTHONPATH=/caminho/para/hostile python3 -m unittest discover -s tests
```

**Compatibilidade cliente/servidor:** se existir uma API no âmbito da mudança,
usa o schema e as ferramentas documentados pelo serviço. Aceder a um endpoint
real pode contactar o host e expor informação; exige autorização e filtra a
saída.

**Executáveis da release:** se o workflow gerar launchers, compara o caminho do
shebang e o interpretador no artefacto construído, sem assumir um tipo de venv
ou diretório de staging.

## Ordem de revisão

1. O que muda no host, ficheiro a ficheiro, comparado com o instalado.
2. Quem corre o quê, com que identidade e com que grupos.
3. O que acontece aos *outros* serviços (dependências, reinícios, portas).
4. O rollback: existe, é um comando, e foi testado?
5. As verificações do script: que evidência existe? Executa sondas contra a
  máquina apenas com autorização e acesso apropriado; caso contrário, indica o
  que o operador deve verificar e marca essa parte como não verificada.
6. Só no fim, a qualidade do código.

## Sinais de alarme

- "Os testes passaram" sem dizer em que ambiente.
- Verificação que compara strings de ficheiros e nada mais.
- Um health check que só prova que o processo está vivo.
- Readiness que aceita o estado anterior à mudança como prova; usa evidência
  posterior à ativação (um heartbeat novo, se aplicável). Um catálogo de falhas
  pode servir de referência se estiver disponível, mas não é dependência.
- Um script root que corre a partir de um diretório onde o utilizador escreve.
- Um PR que muda permissões sem dizer quem deixa de conseguir ler o quê.

## Quando não aplicar

Alterações sem efeito no host de produção (por exemplo, lógica local, docs ou
testes) não precisam desta Skill. Usa-a apenas quando a proposta altera ou
afeta o host de produção, como configuração instalada, deploy, execução
privilegiada, permissões, identidade ou credenciais consumidas por serviços.

## Sondar sem expor segredos

As sondas atravessam sítios onde há credenciais. Regras fixas:

- imprime **nomes de chaves**, nunca valores (`cut -d= -f1`);
- mascara DSNs e tokens antes de mostrar qualquer linha;
- se surgir um valor secreto, não o reproduzas nem o incluas em logs ou
  relatórios. Segue o processo aprovado de resposta a incidentes; rotação ou
  revogação exige autorização e procedimento operacional aplicável.

## Referências

- `references/probes.md`: sondas por tema, prontas a colar.
- Se existir no catálogo, `diagnose-host-failures` pode sugerir hipóteses para
  sintomas correspondentes; não é uma dependência nem substitui a verificação
  das condições reais.
