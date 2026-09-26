# Sondas, por tema

Todas são de leitura. Nenhuma altera o host.

## Estado geral

```bash
systemctl list-units 'PREFIXO-*' --all --no-pager
systemctl show UNIT -p User -p Group -p ExecStart -p WorkingDirectory \
  -p ProtectHome -p NoNewPrivileges -p ProtectSystem -p Restart -p RestartUSec
systemctl list-dependencies --reverse --plain UNIT
systemd-analyze verify /etc/systemd/system/UNIT   # devolve 0 se está consistente
```

## Repositório versus instalado

```bash
sha256sum /usr/local/libexec/PROJ/EXEC
git show origin/main:caminho/no/repo | sha256sum
git -C REPO status --porcelain --untracked-files=all   # árvore limpa?
git -C REPO rev-parse HEAD                              # igual ao main remoto?
```

## Processos

```bash
pid=$(systemctl show UNIT -p MainPID --value)
tr '\0' '\n' < /proc/$pid/environ | cut -d= -f1     # só nomes de chaves
readlink -f /proc/$pid/cwd
tr '\0' ' ' < /proc/$pid/cmdline
```

## Identidades e privilégios

```bash
id UTILIZADOR
getent group docker lxd sudo          # quem é root efetivo sem o parecer
sudo -n -l                            # o que passa sem password
setpriv --no-new-privs sudo -n -l     # reproduzir NoNewPrivileges
ls -la /etc/sudoers.d/
pkaction --version; systemctl is-active polkit
```

## Credenciais SSH

```bash
awk '/^Host /{h=$2} /IdentityFile/{print h" -> "$2}' ~/.ssh/config
ssh -G github.com | grep -E '^(hostname|identityfile) '
GIT_SSH_COMMAND="ssh -i CHAVE -o IdentitiesOnly=yes -o BatchMode=yes" \
  git ls-remote REPO refs/heads/main                       # tem leitura?
GIT_SSH_COMMAND="ssh -i CHAVE -o IdentitiesOnly=yes -o BatchMode=yes" \
  git push --dry-run REPO HEAD:refs/heads/probe-nunca-criada   # tem escrita?
```

## Releases e imutabilidade

```bash
for l in /srv/PROJ/current/*; do echo "$(basename $l) -> $(readlink $l)"; done
find RELEASE -type l | while read l; do
  printf '%s -> %s\n' "$l" "$(readlink -f "$l" 2>/dev/null || echo QUEBRADO)"
done
stat -c '%U:%G %a %n' RELEASE/*
head -1 RELEASE/.venv/bin/CLI    # shebang aponta para onde?
```

## Compatibilidade de API entre cliente e servidor

```bash
curl -s SERVIDOR/openapi.json -o /tmp/spec.json
VENV/bin/python -c "
import json; from pkg.schemas import Modelo
s=json.load(open('/tmp/spec.json'))['components']['schemas']['Modelo']
print('servidor recusa extras:', s.get('additionalProperties'))
print('só no cliente:', sorted(set(Modelo.model_fields) - set(s.get('properties',{}))))"
```

## Backups e recuperação

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

```bash
PYTHONPATH=hostile python3 -m unittest discover -s tests
```
