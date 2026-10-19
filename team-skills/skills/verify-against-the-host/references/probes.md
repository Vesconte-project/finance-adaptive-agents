# Exemplos de sondas, por tema

Estes exemplos não são garantidamente read-only nem seguros para qualquer host.
Antes de os usar, confirma sistema, caminho, unidade, identidade, autorização e
necessidade. Alguns contactam remotos, executam código ou podem revelar dados.
Se não houver acesso aprovado, pede a evidência ao operador e declara o que não
foi verificado. Filtra/redige a saída antes de a partilhar.

## Estado geral

Só num host Linux/systemd confirmado e com acesso autorizado. `systemctl cat`
e `show` podem revelar argumentos ou valores sensíveis; não partilhes a saída
bruta.

```bash
systemctl list-units 'PREFIXO-*' --all --no-pager
systemctl show UNIT -p User -p Group -p ExecStart -p WorkingDirectory \
  -p ProtectHome -p NoNewPrivileges -p ProtectSystem -p Restart -p RestartUSec
systemctl list-dependencies --reverse --plain UNIT
systemd-analyze verify /etc/systemd/system/UNIT   # devolve 0 se está consistente
```

## Repositório versus instalado

Substitui paths, remote e ref pelos valores confirmados no repositório e no
host. `git ls-remote` (se usado) contacta um serviço externo e requer
autorização.

```bash
set -o pipefail
if ! git -C "$REPO" cat-file -e "$REVIEWED_SHA:$UNIT_FILE"; then
  printf '%s\n' 'Não foi possível resolver o ficheiro no commit revisto.' >&2
  exit 1
fi
git -C "$REPO" show "$REVIEWED_SHA:$UNIT_FILE" | sha256sum || exit 1
sha256sum "$INSTALLED_UNIT_FILE" || exit 1
git -C "$REPO" status --porcelain --untracked-files=all || exit 1
git -C "$REPO" rev-parse HEAD || exit 1
```

Os quatro parâmetros identificam o repositório, commit, caminho nesse commit e
ficheiro instalado confirmados para a revisão. Compara os dois digests; imprimir
dois hashes não afirma igualdade. Uma falha torna a comparação inconclusiva.

## Processos

Num host Linux/systemd confirmado, obtém o PID do serviço autorizado e executa a
leitura com uma identidade que já tenha acesso. Não alargues permissões para
fazer passar a sonda; ausência de acesso é verificação não realizada.

```bash
pid=$(systemctl show UNIT -p MainPID --value) || exit 1
python3 - "$pid" <<'PY'
import json
import sys
from pathlib import Path

pid = sys.argv[1]
if not pid.isascii() or not pid.isdecimal() or int(pid) <= 0:
    raise SystemExit("PID inválido; ambiente não verificado.")
entries = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
names = []
for entry in entries:
    if not entry:
        continue
    name, separator, _ = entry.partition(b"=")
    if not separator or not name:
        raise SystemExit("Entrada inválida; ambiente não verificado.")
    names.append(name.decode("utf-8", errors="backslashreplace"))
for name in names:
    print(json.dumps(name, ensure_ascii=True))
PY
```

A sonda exige Python 3 e acesso autorizado ao PID. Falhas de leitura ou análise
têm de permanecer falhas, não uma lista vazia interpretada como sucesso. Os
nomes são strings JSON, uma por linha; quebras de linha e caracteres de controlo
ficam escapados. Nunca uses `tr` para converter o ambiente bruto em linhas antes
de extrair os nomes. `/proc/.../environ` mostra o ambiente inicial, não
necessariamente a configuração consumida agora. Para o diretório de trabalho,
`readlink -f "/proc/$pid/cwd"` é uma leitura separada, se estiver autorizada.
A linha de comando pode conter tokens; não a imprimas sem filtragem e autorização.

Semântica do formato e limites da leitura: [proc_pid_environ(5)](https://man7.org/linux/man-pages/man5/proc_pid_environ.5.html)
e [environ(7)](https://man7.org/linux/man-pages/man7/environ.7.html), consultados em 2026-10-19.

## Identidades e privilégios

Só quando Linux e estas ferramentas estiverem presentes e a inspeção for
autorizada. Group membership ou saída de `sudo -l` não provam, isoladamente, o
alcance efetivo do processo.

```bash
id UTILIZADOR
getent group docker lxd sudo          # quem é root efetivo sem o parecer
sudo -n -l                            # o que passa sem password
setpriv --no-new-privs sudo -n -l     # reproduzir NoNewPrivileges
ls -la /etc/sudoers.d/
pkaction --version; systemctl is-active polkit
```

## Credenciais SSH

Prefere consultar as permissões efetivas no provider. `ls-remote` contacta o
remoto e demonstra apenas leitura. Evita sondas de escrita; `git push --dry-run`
não é prova conclusiva, sobretudo em providers com hooks, branches protegidos ou
políticas próprias.

```bash
awk '/^Host /{h=$2} /IdentityFile/{print h" -> "$2}' ~/.ssh/config
ssh -G github.com | grep -E '^(hostname|identityfile) '
GIT_SSH_COMMAND="ssh -i CHAVE -o IdentitiesOnly=yes -o BatchMode=yes" \
  git ls-remote REPO refs/heads/main                       # tem leitura?
```

Usa o comando remoto apenas com autorização e sem expor credenciais ou URLs
com tokens; interpreta erros segundo a documentação do provider.

## Releases e imutabilidade

Os caminhos seguintes são exemplos: substitui-os apenas por releases cuja
origem foi confirmada e que tens autorização para inspecionar.

```bash
for l in /srv/PROJ/current/*; do echo "$(basename $l) -> $(readlink $l)"; done
find RELEASE -type l | while read l; do
  printf '%s -> %s\n' "$l" "$(readlink -f "$l" 2>/dev/null || echo QUEBRADO)"
done
stat -c '%U:%G %a %n' RELEASE/*
head -1 RELEASE/.venv/bin/CLI    # shebang aponta para onde?
```

## Compatibilidade de API entre cliente e servidor

Só consulta um endpoint real se a API, autenticação e acesso estiverem
confirmados e autorizados. A resposta pode revelar schema interno; guarda-a num
destino aprovado, filtra a saída e usa `-f` para não confundir erros HTTP com
respostas válidas.

```bash
curl -fsS SERVIDOR/openapi.json -o DESTINO_APROVADO/spec.json
VENV/bin/python -c "
import json; from pkg.schemas import Modelo
s=json.load(open('DESTINO_APROVADO/spec.json'))['components']['schemas']['Modelo']
print('servidor recusa extras:', s.get('additionalProperties'))
print('só no cliente:', sorted(set(Modelo.model_fields) - set(s.get('properties',{}))))"
```

## Backups e recuperação

Só consulta timers, resultados e logs se o host usar systemd e houver
autorização. Logs e nomes de backups podem conter informação sensível; filtra e
redige antes de partilhar.

```bash
systemctl list-timers --all --no-pager
systemctl show UNIT -p Result -p ExecMainStatus -p ExecMainExitTimestamp
journalctl -u UNIT --since "48 hours ago" | grep -iE "r2|rclone|Transferred|error"
ls -la DESTINO_DOS_DUMPS | tail -3
```

## Suite de testes como o CI a corre

`hostile/sitecustomize.py`:

```python
import pwd, grp
_pw, _gr = pwd.getpwnam, grp.getgrnam
CONTAS = {"CONTA_DE_DEPLOY", "CONTA_DO_RUNNER", "CONTA_DE_BACKUP"}
GRUPOS = {"GRUPO_DE_DEPLOY", "GRUPO_DE_DESENVOLVIMENTO"}
pwd.getpwnam = lambda n: (_ for _ in ()).throw(KeyError(n)) if n in CONTAS else _pw(n)
grp.getgrnam = lambda n: (_ for _ in ()).throw(KeyError(n)) if n in GRUPOS else _gr(n)
```

Executa a suite apenas num checkout e ambiente de teste aprovados; os testes
executam código e podem alterar ficheiros ou contactar serviços.

```bash
PYTHONPATH=hostile python3 -m unittest discover -s tests
```
