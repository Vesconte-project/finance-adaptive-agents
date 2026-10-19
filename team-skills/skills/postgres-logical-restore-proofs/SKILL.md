---
name: postgres-logical-restore-proofs
description: Desenhar, rever ou diagnosticar uma prova de restauro de um dump lógico PostgreSQL (pg_dumpall de roles mais pg_dump plain, restaurados por psql numa base descartável, por exemplo num contentor da imagem oficial). Usa quando o teste de restauro falha sem causa clara, quando o produtor do dump morre com SIGPIPE, ou ao preparar um restauro em PostgreSQL 16 ou posterior. Não para backups físicos (pg_basebackup, WAL) nem para restauros de produção.
---

# A prova de restauro tem de falhar pela razão certa

Uma prova de restauro existe para responder a uma pergunta: "se perdermos a
base, este backup volta?". A resposta só vale se a prova **falhar quando o
backup não serve** e **passar quando serve**. Num restauro lógico em pipe
(`dump | psql`) há várias formas de a prova falhar por razões que nada têm a ver
com o backup, e de a causa real se perder.

Evidência: incidente de 19/10/2026, PostgreSQL 16.13, imagem oficial `postgres:16`,
dump plain transmitido por restic para `psql -v ON_ERROR_STOP=1`. Um restauro
mensal tinha passado a 04/10 com o mesmo código. A 19/10 falhou três vezes
seguidas, por três causas diferentes, nenhuma delas um backup mau.

## 1. O erro do recetor é o primário; o SIGPIPE do produtor é consequência

Quando o `psql` para no primeiro erro, fecha o stdin. O produtor (restic,
`pg_dump`, `zcat`…) ainda está a escrever e morre com SIGPIPE (`-13`, ou 141 no
shell). Se o código reportar primeiro a saída do produtor, o relatório diz
"falha do restic" e o erro SQL, que é a causa, perde-se.

- Captura o stderr do `psql` em memória limitada e extrai **só** o SQLSTATE, o
  número da linha e a categoria da instrução (`-v VERBOSITY=sqlstate
  -v SHOW_CONTEXT=never`). Nunca escrevas o stderr cru: pode conter valores de
  dados.
- Reporta o código de saída do `psql` como primário e o do produtor como
  secundário.
- Depois de o `psql` falhar, **drena** o resto do stream para `/dev/null` em vez
  de fechar o pipe. Assim o produtor termina normalmente e não deixa locks
  pendurados (o restic, por exemplo, pode deixar o repositório bloqueado).

Sinal: `exit -13` no produtor e o contentor de restauro a viver só alguns
segundos. Olha para o recetor, não para o armazenamento remoto.

## 2. "Pronto" na imagem oficial pode ser o servidor temporário

O entrypoint da imagem oficial arranca primeiro um servidor **temporário**, só
com socket Unix, para criar a base e o utilizador. Depois para-o e arranca o
servidor final. `pg_isready` (e qualquer ligação por socket) pode responder
"pronto" ao servidor temporário; o restauro começa, o servidor desliga-se para
reiniciar e o `psql` falha.

- Espera por uma consulta real (`SELECT 1`) **por TCP** (`-h 127.0.0.1`) na base
  alvo, com o utilizador alvo. O servidor temporário não escuta TCP.
- Usa o mesmo transporte para o restauro e para as verificações finais.
- É uma corrida: pode passar durante semanas e falhar num dia qualquer. Um
  sucesso anterior não prova que a espera está certa.

## 3. PostgreSQL 16: memberships `GRANTED BY` exigem a mesma identidade de arranque

A partir do PG16, o `pg_dumpall --roles-only` regista quem concedeu cada
membership de role (`GRANT a TO b … GRANTED BY x`). Se em produção `x` é o
superuser de arranque (o criado por `POSTGRES_USER`, OID 10) e o cluster
descartável arranca com **outro** utilizador de arranque, `x` passa a ser um
superuser normal e o PG16 recusa reproduzir essas concessões. Ser superuser não
chega.

- Arranca o cluster descartável com o **mesmo nome de utilizador de arranque**
  que produção.
- O dump vai então tentar criar uma role que já existe (`CREATE ROLE <bootstrap>;`).
  Dispensa **só essa instrução exata, uma vez**, e exige que o `ALTER ROLE
  <bootstrap> WITH …` seguinte aplique os atributos. Qualquer outro erro, incluindo
  `CREATE ROLE` de outra role, continua a parar o restauro.
- Não filtres por texto livre: um filtro ingénuo pode apanhar linhas dentro de
  `COPY` ou corpos de funções. Trabalha nas fronteiras de instrução da secção de
  roles.
- No fim, compara o catálogo restaurado (`pg_roles`: atributos; `pg_auth_members`:
  role, membro, grantor, `admin_option`, `inherit_option`, `set_option`) com o
  que o próprio dump declara. Uma prova que só conta linhas de tabelas não
  apanha roles e permissões erradas.

Isto só aparece quando passam a existir memberships concedidas desta forma, por
exemplo depois de introduzir roles de capacidade e logins separados. Uma prova
que passava antes pode começar a falhar sem nenhuma alteração no código do backup.

## 4. Lê o output como produção o lê

`psql -c "SET …; SELECT json_build_object(…)"` sem `-q` escreve a etiqueta
`SET` antes do JSON, e o parser falha. Os testes usavam `-q`; o código real não.

- O teste tem de chamar o **mesmo leitor** que o runtime usa (mesma função,
  mesmas flags), não uma reimplementação.
- Para ler valores, usa `-X -qAt` e valida a forma do resultado; uma falha de
  leitura é um erro próprio (por exemplo `role_catalog_read_failed`), não um
  JSON inválido genérico.

## Ordem de diagnóstico

1. Quanto tempo viveu o contentor de restauro, e houve OOM no kernel? Segundos
   sem OOM apontam para um erro SQL cedo (roles ou primeiro DDL), não para
   volume de dados.
2. Qual é o SQLSTATE e em que secção? Se o runtime o perdeu, corrige primeiro o
   diagnóstico (ponto 1). Não adivinhes a causa nem repitas a prova.
3. Compara com o último restauro bom: mesmas versões? (`PG_VERSION` da imagem
   local versus produção). Se as versões são iguais, mudou o **conteúdo** do
   dump: roles, memberships, extensões.
4. Reproduz numa base vazia descartável, sem dados de produção, antes de mexer
   no runtime.

## Quando não aplicar

Backups físicos e PITR têm outros modos de falha. Num restauro feito pelo
próprio cluster de produção, com o mesmo utilizador de arranque, os pontos 2 e
3 não se aplicam.

## Relacionadas

- `production-faithful-integration-proofs`: quando uma prova descartável difere
  de produção.
- `cloudflare-r2-backups-and-bucket-lock`: falhas do lado do armazenamento.
- `guards-that-pass-blindly`: uma prova que conta linhas e não roles passa sem ver.
