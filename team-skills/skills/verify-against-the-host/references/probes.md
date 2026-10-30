# Exemplos de sondas, por tema

Estes exemplos não são garantidamente read-only nem seguros para qualquer host.
Antes de os usar, confirma sistema, caminho, unidade, identidade, autorização e
necessidade. Alguns contactam remotos, executam código ou podem revelar dados.
Se não houver acesso aprovado, pede a evidência ao operador e declara o que não
foi verificado. Filtra/redige a saída antes de a partilhar. Executa os blocos como scripts ou
numa subshell apropriada: `exit` termina a shell e opções como `pipefail`
persistem se forem coladas diretamente numa sessão interativa.

## Estado geral

Só num host Linux/systemd confirmado e com acesso autorizado. `systemctl cat`
e `show` podem revelar argumentos ou valores sensíveis; não partilhes a saída
bruta.

```bash
systemctl list-units 'PREFIXO-*' --all --no-pager
systemctl show UNIT -p User -p Group -p ExecStart -p WorkingDirectory \
  -p ProtectHome -p NoNewPrivileges -p ProtectSystem -p Restart -p RestartUSec
systemctl list-dependencies --reverse --plain UNIT
systemd-analyze verify /etc/systemd/system/UNIT   # diagnóstico estático; não prova execução
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
ssh -G HOST_CONFIRMADO | grep -E '^(hostname|identityfile) '
GIT_SSH_COMMAND="ssh -i CHAVE -o IdentitiesOnly=yes -o BatchMode=yes" \
  git ls-remote REPO REF_CONFIRMADA                       # tem leitura?
```

Usa o comando remoto apenas com autorização e sem expor credenciais ou URLs
com tokens; interpreta erros segundo a documentação do provider.

## Releases e imutabilidade

Os caminhos seguintes são exemplos: substitui-os apenas por releases cuja
origem foi confirmada e que tens autorização para inspecionar.

Com Python 3 disponível, a sonda seguinte enumera symlinks sem percorrer
subdiretórios que sejam symlinks. Confirma também autorização para resolver os
seus destinos; não amplia acesso. Emite JSON por registo, escapando nomes com
newlines, e termina com código não zero se a enumeração ou resolução falhar.
`inconclusive` não significa link quebrado: pode ser falta de acesso, alvo
ausente, loop ou uma mudança concorrente.

```bash
python3 - "$RELEASE" <<'PY'
import json
import os
import stat
import sys
from pathlib import Path

failures = 0
count = 0

def emit(record):
    print(json.dumps(record, ensure_ascii=True))

def walk_error(error):
    global failures
    failures += 1
    emit({"path": os.fsdecode(error.filename) if error.filename else None,
          "status": "inconclusive", "error": type(error).__name__})

try:
    root = Path(sys.argv[1]).resolve(strict=True)
    if not stat.S_ISDIR(root.stat().st_mode):
        raise NotADirectoryError(str(root))
except (OSError, RuntimeError) as error:
    emit({"status": "inconclusive", "error": type(error).__name__})
    raise SystemExit(1)

for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
    for name in sorted(dirs + files):
        path = Path(directory) / name
        try:
            if not stat.S_ISLNK(path.lstat().st_mode):
                continue
            count += 1
            target = path.resolve(strict=True)
            emit({"path": str(path.relative_to(root)), "status": "resolved",
                  "target": str(target)})
        except (OSError, RuntimeError) as error:
            failures += 1
            emit({"path": str(path.relative_to(root)), "status": "inconclusive",
                  "error": type(error).__name__})
emit({"symlinks": count, "failures": failures})
raise SystemExit(1 if failures else 0)
PY
```

A lista vazia não prova que existiam links nem que a release é íntegra. Uma
resolução é uma observação momentânea; compara inventário e destinos com o
contrato esperado e considera mudanças concorrentes. Não altera links nem
conclui igualdade de releases. Para o launcher Python, se existir, inspeciona
separadamente o shebang do CLI confirmado e testa-o só no ambiente autorizado.

## Compatibilidade de API entre cliente e servidor

Só consulta um endpoint real se a API, autenticação e acesso estiverem
confirmados e autorizados. A resposta pode revelar schema interno; guarda-a num
destino aprovado, filtra a saída e usa `-f` para não confundir erros HTTP com
respostas válidas. O exemplo Python executa código do projeto e pressupõe
Pydantic v2 (`model_fields`) e aquele schema OpenAPI; confirma esses contratos
antes de o usar. Uma falha de transporte/HTTP interrompe o bloco antes da
comparação: um ficheiro existente ou parcial não é evidência desta consulta.
Não reutilizes esse destino como resposta válida depois de uma falha.

```bash
curl -fsS SERVIDOR/openapi.json -o DESTINO_APROVADO/spec.json || exit 1
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
journalctl -u UNIT --since "48 hours ago" | grep -iE "PADRAO_CONFIRMADO_DO_BACKUP"
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

O `sitecustomize.py` acima simula só `pwd.getpwnam` e `grp.getgrnam` para os
nomes indicados. Não cobre `getpwuid`, `getgrgid`, subprocessos como `id` nem
outros mecanismos de resolução; um teste verde não prova ausência de todas
as dependências de contas locais.

## Factos do host que partem código revisto

Casos reais (2026-10) em que código com testes verdes falhou no host. Antes de dar uma mudança
por pronta, confirma estes factos no host alvo:

- **Tipo de filesystem de cada caminho que entra num cálculo de capacidade.** Um `/tmp` em
  tmpfs (RAM) nunca tem uma reserva de 20 GiB. Uma regra de capacidade aplicada a todos os
  filesystems recusou todas as builds. Para cada caminho, obtém o `st_dev` e procura o tipo em
  `/proc/self/mountinfo`.

  ```bash
  findmnt -no FSTYPE,SIZE,AVAIL --target /tmp
  ```

- **`systemctl show` recusa unidades template** (`nome@.service`, sem instância). Um inventário
  que passa a lista de `list-unit-files` diretamente ao `show` falha sempre num host com
  templates. Os templates leem-se com `systemctl cat`; as instâncias, com
  `list-units --all`. Unidades falhadas aparecem com `●` no início da linha.

  ```bash
  systemctl --no-pager list-unit-files --type=service,timer --no-legend --plain | awk '$1 ~ /@\./' | head
  ```

- **"active" não quer dizer "a aceitar ligações".** Depois de um restart, o systemd marca o
  serviço como ativo antes de a aplicação abrir a porta. Uma verificação de saúde feita logo a
  seguir apanhou `URLError` e acionou um rollback desnecessário. Faz polling da saúde, com um
  prazo (por exemplo 90 s), e trata recusa de ligação e timeout como "ainda não", não como falha.
- **Um bind parameter escondido num literal SQL.** Num `text()` do SQLAlchemy, um regex como
  `(?:Error` dentro do SQL é lido como o parâmetro `:Error`, e o resultado é `StatementError`. Escapa os
  dois pontos ou passa o padrão como parâmetro, e testa a compilação do SQL (os binds
  esperados) sem ligação à base.
