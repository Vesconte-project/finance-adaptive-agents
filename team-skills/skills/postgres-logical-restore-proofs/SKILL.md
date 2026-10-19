---
name: postgres-logical-restore-proofs
description: Desenhar, rever ou diagnosticar uma prova de restauro de um dump lógico PostgreSQL (pg_dumpall de roles mais pg_dump plain, restaurados por psql numa base descartável, por exemplo num contentor da imagem oficial). Usa ao preparar ou diagnosticar esta prova descartável, incluindo falhas sem causa clara, SIGPIPE no produtor ou reprodução de roles e memberships em PostgreSQL 16 ou posterior. Não para backups físicos (pg_basebackup, WAL) nem para restauros de produção.
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
seguidas, por três causas diferentes, nenhuma delas um backup mau. Estes são
factos do incidente, não evidência sobre a instalação atual. Antes de aplicar
uma receita, obtém versões de cliente/servidor, imagem e entrypoint reais,
estado de inicialização, transporte e erros sanitizados. Sem esses factos,
pede a informação em falta e mantém as hipóteses explícitas. Trabalha apenas
num destino descartável autorizado; um dump pode conter dados, passwords de
roles e SQL executável, pelo que precisa de isolamento e tratamento de segredo.

## 1. Preserva os dois erros antes de atribuir causalidade

Quando o `psql` para e fecha o stdin, um produtor que ainda escreva pode
receber SIGPIPE (`-13` em certas APIs de subprocessos, 141 em alguns shells).
Isso é compatível com falha anterior do recetor, mas SIGPIPE sozinho não prova
a causa. Confirma a ordem dos eventos; preserva também erros independentes do
produtor, incluindo leitura remota, integridade ou descodificação.

- Captura separadamente os estados de saída, timeout/cancelamento e diagnóstico
  dos dois processos; o exit code final de um pipe não basta. Apresenta o erro
  SQL como primário apenas quando a evidência estabelecer essa cadeia causal.
- Recolhe stderr com consumo concorrente e retenção limitada, para não bloquear
  em pipes cheios. Com `-v VERBOSITY=sqlstate -v SHOW_CONTEXT=never`, extrai só
  SQLSTATE, linha e categoria quando disponíveis. Aplica uma allowlist ao que
  sai no relatório: flags de verbosidade não tornam todo o stderr seguro.
  Não registes SQL, valores, passwords nem stderr cru.
- Após falha, escolhe limpeza limitada ao workflow: drenar para um sumidouro
  pode deixar um produtor finito terminar, mas define antes limites de tempo e
  bytes/custo. Se excedidos, cancela/termina apenas os subprocessos que a prova
  criou, conforme a ferramenta; recolhe os seus estados com espera limitada.
  Drena e descarte não significam validação do backup.
- Não prometas que drenar evita locks. Confirma o encerramento e eventual lock
  segundo a ferramenta; se a limpeza não estiver confirmada, reporta-a como
  incompleta. Não executes unlock nem removas locks automaticamente, sobretudo
  quando possa haver outro processo ativo.

Um produtor com SIGPIPE e um contentor que viveu segundos justificam procurar
o erro do recetor, sem excluir falha do produtor ou do ambiente.

## 2. Verifica qual servidor respondeu à prontidão

Na inicialização de um diretório vazio, o entrypoint da imagem oficial
PostgreSQL consultado arranca um servidor temporário só com socket Unix, faz
a inicialização, para-o e lança o servidor final. Nesse percurso, uma sonda
por socket pode aceitar o temporário. Isto não estabelece o comportamento de
outra imagem, entrypoint alterado ou diretório já inicializado.

- Confirma imagem/digest, entrypoint e percurso de inicialização. Se não forem
  conhecidos, obtém-nos antes de prescrever uma correção.
- Para esse percurso confirmado, espera com prazo finito por uma consulta real
  (`SELECT 1`) por TCP na base e identidade alvo. `-h 127.0.0.1` serve dentro
  do namespace do servidor; fora dele usa o endpoint autorizado da prova.
  Confirma que é o servidor alvo, não outro serviço que escuta nessa porta.
- Usa o transporte relevante para o restauro e verificações finais. Noutras
  imagens, verifica a condição de prontidão apropriada ao seu ciclo de vida.
- Uma corrida pode passar durante semanas; um sucesso anterior não prova que
  a espera está certa.

## 3. PostgreSQL 16: verifica a identidade do grantor de memberships

Em PG16, `pg_dumpall --roles-only` pode preservar o grantor de memberships
(`GRANT a TO b … GRANTED BY x`). O grantor tem de possuir `ADMIN OPTION` sobre
a role concedida, salvo se for o bootstrap superuser. No incidente, `x` era
a identidade de bootstrap da origem e o destino usava outro nome: recriar
`x` como superuser comum não reproduzia essa exceção.

- Confirma o erro de membership e os grantors no dump; identifica o bootstrap
  real da origem e do destino com evidência autorizada. O `POSTGRES_USER`
  atual não prova quem inicializou um volume existente. Não deduzas esta causa
  apenas da versão do servidor ou de uma role ser superuser.
- Se esse desvio for confirmado, inicializar um **novo cluster descartável**
  com o mesmo nome de bootstrap da origem é uma opção para preservar a
  semântica. Não reinicializes um volume existente nem alteres produção. Para
  grantors comuns, reproduz as concessões e opções necessárias declaradas no
  dump, em vez de os transformar em bootstrap para contornar uma falha.
- Se o dump criar a role de bootstrap que já existe no destino, uma adaptação
  pode dispensar **só essa instrução exata, uma vez**, na secção de roles
  identificada; exige a aplicação do `ALTER ROLE` correspondente e dos seus
  atributos esperados. Qualquer outro erro continua a parar o restauro. Sem
  fronteiras SQL fiáveis, não filtres: prepara uma reprodução mínima antes.
- Não filtres por texto livre: linhas dentro de `COPY` ou corpos de funções
  podem coincidir. Conserva o artefacto original e regista a adaptação.
- Compara no fim `pg_roles` (atributos) e `pg_auth_members` (role, membro,
  grantor, `admin_option`, `inherit_option`, `set_option`) por identidades
  lógicas, não por igualdade de OIDs entre clusters, com o que o dump declara.
  Só contar linhas de tabelas não prova roles nem permissões.

Memberships novas podem expor este desvio sem alteração no código de backup;
é uma hipótese a testar, não uma conclusão a partir do histórico.

## 4. Lê o output como produção o lê

`psql -c "SET …; SELECT json_build_object(…)"` sem `-q` escreve a etiqueta
`SET` antes do JSON, e o parser falha. Os testes usavam `-q`; o código real não.

- O teste tem de chamar o **mesmo leitor** que o runtime usa (mesma função,
  mesmas flags), não uma reimplementação.
- Para ler valores, usa `-X -qAt` e valida a forma do resultado; uma falha de
  leitura é um erro próprio (por exemplo `role_catalog_read_failed`), não um
  JSON inválido genérico.

## Ordem de diagnóstico

1. Quanto tempo viveu o contentor e o que mostram os eventos disponíveis e
   autorizados (incluindo OOM)? Uma saída precoce pode ser SQL, prontidão,
   autenticação ou recursos. Ausência de evidência de OOM não o exclui.
2. Qual é o SQLSTATE e em que secção, e o que aconteceu ao produtor? Se o
   runtime perdeu a evidência, corrige o diagnóstico antes de uma nova
   tentativa autorizada; não uses retries sucessivos para adivinhar a causa.
3. Compara com o último restauro bom: versões efetivas dos servidores e
   clientes, imagem/digest, entrypoint, configuração, extensões, recursos e
   conteúdo do dump. `PG_VERSION` indica a versão major do diretório, não a
   versão exata do servidor. Versões iguais não excluem corridas de arranque
   nem outras diferenças ambientais; alteração de conteúdo é uma hipótese.
4. Reproduz numa base vazia descartável, sem dados de produção, antes de mexer
   no runtime.

## Quando não aplicar

Backups físicos, PITR e restauros de produção ficam fora deste âmbito. Um
bootstrap igual ou um volume já inicializado podem eliminar certas diferenças
do incidente, mas não dispensam verificar prontidão e permissões relevantes.

## Fontes técnicas e limites

Consultadas em 19/10/2026: [GRANT em PostgreSQL 16](https://www.postgresql.org/docs/16/sql-grant.html),
[código de pg_dumpall da série 16](https://github.com/postgres/postgres/blob/REL_16_STABLE/src/bin/pg_dump/pg_dumpall.c),
[variáveis do psql](https://www.postgresql.org/docs/16/app-psql.html) e
[entrypoint oficial PostgreSQL](https://github.com/docker-library/postgres/blob/master/docker-entrypoint.sh).
Estas fontes sustentam os mecanismos descritos; não substituem uma reprodução
na versão/imagem exatas nem certificam a adaptação SQL ou o tratamento de
subprocessos de um projeto.

## Relacionadas (leitura opcional, se disponíveis)

- `production-faithful-integration-proofs`: quando uma prova descartável difere
  de produção.
- `cloudflare-r2-backups-and-bucket-lock`: falhas do lado do armazenamento.
- `guards-that-pass-blindly`: uma prova que conta linhas e não roles passa sem ver.
