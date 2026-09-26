---
name: verify-against-the-host
description: Rever alterações de infraestrutura (units systemd, scripts root, deploys, permissões) contra o estado real da máquina antes de as aplicar. Usa quando um agente ou um PR propõe mexer num host de produção, quando um script root vai correr pela primeira vez, ou quando alguém diz "os testes passaram" sobre código que toca no sistema.
---

# Verificar contra o host, não contra o repositório

A maior parte dos erros que chegam a produção não vêm de desenho fraco. Vêm de
o autor ter escrito a partir do repositório enquanto a máquina tinha outra
coisa instalada.

## Regra

Antes de aprovar qualquer alteração que toque no host, compara o que o PR
assume com o que a máquina tem. Se não conseguires mostrar o comando que o
confirma, não está verificado.

## As sondas que mais valem

**Drift entre o repositório e o instalado.** Nunca partas do ficheiro do repo.

```bash
for f in systemd/*.service; do
  a=$(git show origin/main:$f | sha256sum | cut -c1-12)
  b=$(sha256sum /etc/systemd/system/$(basename $f) 2>/dev/null | cut -c1-12)
  [ "$a" = "$b" ] || echo "DIFF $(basename $f)"
done
```

**O ambiente real de um serviço** (nomes de chaves e caminhos; nunca valores):

```bash
pid=$(systemctl show UNIT -p MainPID --value)
tr '\0' '\n' < /proc/$pid/environ | cut -d= -f1
```

Um `.env` no repositório não prova nada. O que conta é o que o processo tem.

**Dependências entre units**, antes de parar ou reiniciar seja o que for:

```bash
systemctl list-dependencies --reverse --plain UNIT
```

`Requires=` propaga o *stop*, mas o *start* seguinte não repõe os dependentes.

**Reproduzir restrições de sandbox** sem tocar em produção:

```bash
setpriv --no-new-privs sudo -n -l   # prova que NoNewPrivileges mata o sudo
```

**Correr a suite como o CI a corre**, sem as contas Unix locais. Um
`sitecustomize.py` que faz `pwd.getpwnam` e `grp.getgrnam` falhar para as
contas de produção apanha testes que só passam nesta máquina:

```bash
PYTHONPATH=/caminho/para/hostile python3 -m unittest discover -s tests
```

**Compatibilidade cliente/servidor sem escrever nada:** compara o schema que o
servidor publica (`/openapi.json`) com os campos que o cliente envia.

**Executáveis que a release gera:** confirma o shebang e que o interpretador
existe. Scripts criados durante o build podem apontar para diretórios de
staging que já foram renomeados.

## Ordem de revisão

1. O que muda no host, ficheiro a ficheiro, comparado com o instalado.
2. Quem corre o quê, com que identidade e com que grupos.
3. O que acontece aos *outros* serviços (dependências, reinícios, portas).
4. O rollback: existe, é um comando, e foi testado?
5. As verificações do próprio script: já correram alguma vez contra esta
   máquina? Se não, corre-as tu em modo leitura antes de aprovar.
6. Só no fim, a qualidade do código.

## Sinais de alarme

- "Os testes passaram" sem dizer em que ambiente.
- Verificação que compara strings de ficheiros e nada mais.
- Um health check que só prova que o processo está vivo.
- Readiness que aceita o estado anterior como prova (ver o caso do heartbeat
  no catálogo de falhas).
- Um script root que corre a partir de um diretório onde o utilizador escreve.
- Um PR que muda permissões sem dizer quem deixa de conseguir ler o quê.

## Quando não aplicar

Alterações que não tocam no host (código de aplicação com CI a sério, docs,
testes) não precisam disto. Aplica-o a units, scripts root, permissões,
identidades, credenciais e tudo o que corra como root.

## Verificar números, não narrativas

Quando um agente ou um relatório te dá um número, recalcula-o. Foi assim que
apanhei, em dois dias: um hash de contrato cuja diferença era um único campo,
um inventário de 453 MB que afinal eram 432 MB medidos de outra forma, e um
custo de cópia de hardlinks que se revelou zero (e por isso não havia risco de
disco). Em todos, aceitar o resumo teria passado — mas sem saber se estava certo.

- Conta entradas e bytes tu próprio, com o mesmo critério do script.
- Recalcula hashes e compara campo a campo quando não baterem.
- Mede o custo real antes de aprovar (espaço, tempo, memória), em vez de
  aceitar "é pouco".

## Nunca emitas um identificador que não calculaste

Um hash, um fingerprint, um ID: se o escreveste de memória ou por padrão, está
errado e alguém vai comparar com ele. Aconteceu-me: dei o fingerprint de uma
chave que acabara de gerar sem o calcular, e o valor não tinha nada a ver. Custa
um comando:

```bash
ssh-keygen -lf chave.pub          # fingerprint de uma chave
sha256sum ficheiro | cut -c1-16   # hash de um ficheiro
```

E se a chave pública não existir, deriva-a da privada sem a expor:
`ssh-keygen -y -f privada`.

## "O que eu revi" é um SHA, não o nome de um ramo

Guarda o commit exato que revistes e compara contra **esse**. Um ramo move-se:
quando quiseres confirmar que o que entrou no principal é o que aprovaste, o
diff é contra o SHA revisto. Diffar contra a ponta anterior do ramo dá o
resultado oposto ao verdadeiro — e eu quase reportei "código não revisto em
produção" por ter feito exatamente isso, quando o delta eram as correções que eu
próprio tinha pedido.

## Um clone velho mente sobre o que está publicado

Antes de dizeres que um ramo "só existe neste disco", verifica duas coisas que
parecem a mesma e não são: se o ramo está no remoto, e se o *conteúdo* dele está.

Um clone cuja `origin/main` está desatualizada faz três ilusões de uma vez:

- ramos já integrados aparecem como trabalho não publicado (`origin/main..ramo`
  mostra commits que a `main` real já tem);
- `main` local pode apontar para outro commit que não a `main` real — não
  "atrasada", *divergente* — e `git checkout main` dá uma história falsa;
- `refs/remotes/<nome>/...` pode sobreviver a um remote que já não está
  configurado, e então "está numa ref remota" não quer dizer "está no servidor".

As sondas, por esta ordem:

```bash
git ls-remote origin 'refs/heads/*'            # o servidor, não o espelho
git remote -v                                  # a ref remota tem remote a sério?
git rev-parse origin/main                      # == ao ls-remote?
git for-each-ref --contains <sha> refs/remotes  # quem alcança o commit
```

E o teste que resolve a questão de facto: **compara conteúdo, não nomes de
ramos**. O mesmo ficheiro pode ter chegado à `main` por outro caminho, com outro
nome, noutro repositório. Hash normalizado (`grep -v '^#' | sha256sum`) contra
todos os blobs candidatos de todas as `main` responde; `git log` não.

## Uma varredura parcial é pior que nenhuma

Se procuras repositórios com um glob de dois níveis (`*/` e `*/*/`), não digas
"em todo o disco". Clones separados escondem-se mais fundo, e um `worktree list`
não os mostra porque não são worktrees — têm `.git` próprio. Distingue-os:

```bash
find <raiz> -type d -name .git | sed 's#/\.git$##'     # inventário real
git -C <dir> rev-parse --git-dir --git-common-dir       # iguais = clone; != = worktree
```

Quando duas verificações tuas se contradizem, para. Uma está errada, e é mais
provável que seja a que tem o âmbito mais estreito.

## Sondar sem expor segredos

As sondas atravessam sítios onde há credenciais. Regras fixas:

- imprime **nomes de chaves**, nunca valores (`cut -d= -f1`);
- mascara DSNs e tokens antes de mostrar qualquer linha;
- se um segredo aparecer mesmo assim no output, trata-o como exposto: regista,
  avisa, e roda-o. Uma password que passou por um terminal, um log ou um
  transcript deixou de ser secreta.

## Referências

- `references/probes.md`: sondas por tema, prontas a colar.
- Skill `diagnose-host-failures`: catálogo de falhas reais por sintoma. Consulta-o
  sempre que uma verificação falhar de forma inesperada.
