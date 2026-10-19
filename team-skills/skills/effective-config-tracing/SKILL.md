---
name: effective-config-tracing
description: Rastrear uma divergência entre a configuração declarada e a configuração efetiva de um serviço, incluindo alterações ineficazes, um daemon que não carregou um ficheiro novo, ou problemas de acesso após mudar a identidade. Usa quando há evidência dessa divergência; não para erros de parsing ou falhas sem discrepância de configuração.
---

# Onde é que este valor nasce, afinal

A pergunta que resolve incidentes não é "o que diz a configuração", é **"que
valor tem este processo, neste momento, e quem o pôs lá"**. São coisas
diferentes, e a distância entre elas cresce com a idade do sistema.

## Identifica as fontes aplicáveis

Não há uma ordem universal que inclua unit, processo-pai, aplicação e
orquestrador. Se o serviço usar systemd, inspeciona a configuração efetiva da
unit e aplica as regras da versão instalada para o ambiente do manager,
`PassEnvironment=`, `Environment=`, `EnvironmentFile=` e drop-ins. A ordem das
diretivas e dos ficheiros pode importar; confirma-a no sistema alvo, sem
assumir que a última camada de uma lista genérica ganha.

Um wrapper, a aplicação ou um orquestrador pode transformar ou substituir
valores depois do arranque. Trata esses mecanismos como fontes condicionais:
investiga-os apenas se o serviço realmente os usar e identifica qual componente
consome o valor. Um valor guardado noutro sistema não sobrepõe automaticamente
a configuração do host.

## O método

**1. Confirma a plataforma e a autorização.** Os comandos abaixo só se aplicam
se o serviço correr em Linux sob systemd e o operador tiver autorizado a
inspeção. Se não for esse o caso, usa as ferramentas de diagnóstico próprias
do runtime e documenta o que não pode ser verificado.

Quando for aplicável, começa pelo processo, não pelo repositório:

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

Executa a leitura com uma identidade que já tenha acesso aprovado ao PID e com
Python 3 disponível. Se faltar acesso, reporta a verificação como não realizada;
não alargues permissões. O comando imprime nomes do ambiente inicial como strings
JSON escapadas, não valores nem fontes. Separar entradas por NUL antes do primeiro
`=` evita imprimir partes de valores multilinha. Uma falha de leitura/análise não
é uma lista vazia válida. A aplicação pode transformar o ambiente ou carregar
outras fontes; esta sonda isolada não prova o valor que ela consome. Formato e
limites: [proc_pid_environ(5)](https://man7.org/linux/man-pages/man5/proc_pid_environ.5.html)
e [environ(7)](https://man7.org/linux/man-pages/man7/environ.7.html), consultados em 2026-10-19.

**2. Inspeciona a unit e as fontes declaradas sem imprimir valores.**

```bash
systemctl show UNIT -p FragmentPath -p DropInPaths -p EnvironmentFiles
systemctl cat UNIT | sed -n -E '/^[[:space:]]*Environment=/ { s/=.*/=<redacted>/; p; }; /^[[:space:]]*EnvironmentFile=/p'
```

Executa apenas com acesso autorizado. O filtro mostra a presença de `Environment=`
sem os seus valores e mantém as fontes declaradas em `EnvironmentFile=`. Confirma
se a versão instalada suporta `EnvironmentFiles` em `systemctl show`; inspeciona
os drop-ins indicados por `DropInPaths` em vez de assumir um diretório fixo. Não
imprimas o conteúdo dos ficheiros de ambiente.

**3. Investiga fontes externas apenas se existirem no fluxo real.** Se um
orquestrador, agendador ou wrapper lançar o processo, usa a interface e o
esquema documentados para esse sistema; não assumas que existe uma API local.
Por exemplo, se a API e os campos forem confirmados e a consulta estiver
autorizada, extrai apenas os nomes das chaves:

```bash
# exemplo: definições de deployment guardadas na base do orquestrador
curl -s -X POST http://127.0.0.1:PORTA/api/deployments/filter \
  -H 'content-type: application/json' -d '{"limit":200}' \
  | python3 -c "import json,sys; [print(d['name'], sorted((d.get('job_variables') or {}).get('env',{}))) for d in json.load(sys.stdin)]"
```

Imprime **nomes de chaves**, nunca valores. Este endpoint é apenas ilustrativo;
confirma a API real e evita consultas que possam expor credenciais.

**4. Confirma a hipótese com uma verificação de leitura autorizada.** Se a
identidade e os caminhos forem conhecidos e relevantes, verifica as permissões
sem alterar ficheiros:

```bash
sudo -n -u IDENTIDADE true
sudo -n -u IDENTIDADE test -w /caminho
sudo -n -u IDENTIDADE test -x /caminho/pai
```

Executa a primeira verificação antes das restantes. Se falhar, a identidade ou
a autorização `sudo` não estão disponíveis e o resultado é inconclusivo. Para
as verificações `test`, um resultado falso não prova por si só um problema de
permissões: confirma também que o caminho existe e que montagens, ACLs ou outros
controlos não explicam o resultado. Não classifiques falhas de execução ou
autorização como negação de acesso.

## Armadilhas confirmadas

- **O mesmo valor definido em dois sítios**, com precedência implícita. Funciona
  por acaso até alguém mudar a ordem ou remover o sítio errado. Confirma se é
  duplicação acidental ou um override intencional. Propõe remover apenas a
  duplicação desnecessária, após estabelecer a precedência e a autorização.
- **Um symlink que funciona e um pai que não deixa passar.** Um caminho pode
  apontar para o sítio certo e falhar na mesma: para o atravessar, é preciso
  permissão de execução em **todos** os diretórios acima. Um `0750` a meio do
  caminho chega para bloquear uma identidade nova.
- **Mudar a identidade do serviço revela tudo isto de uma vez.** Valores que só
  funcionavam porque o processo corria com o utilizador certo passam a falhar.
  Antes de trocar a identidade de um serviço, traça o caminho real de cada
  caminho e credencial que ele usa.
- **A ordem dos `EnvironmentFile=` pode afetar o resultado.** Confirma a ordem
  aplicável na unit e nos drop-ins da versão instalada; documenta-a se for
  relevante, ou propõe remover duplicação após confirmar o consumidor.

## Calendário declarado num fuso, efeito noutro

Exemplo de risco a verificar: um timer systemd com fuso explícito
(`OnCalendar=Sun *-*-* 02:10:00 Europe/London`) pode corresponder a 01:10 UTC
no horário de verão e a 02:10 UTC no horário de inverno, sem mudar o ficheiro.
Uma janela proibida fixa em UTC pode então passar a coincidir com o arranque.
O relato original está datado de 18/10/2026; sem os recibos e as ocorrências da
versão instalada, não prova que a execução após a transição tenha sido observada.

- Confirma primeiro o fuso e a política da janela aprovada. Se esta for fixa em
  UTC, um timer em UTC pode evitar deslocamentos; se seguir hora civil, a mudança
  pode ser esperada e não constitui, por si, divergência a corrigir.
- Confirma próximas ocorrências na versão instalada e nas datas de transição,
  pela interface suportada; uma listagem feita hoje não prova datas futuras.
- Compara arranque **mais duração medida e margem aprovada** com as janelas
  proibidas. Um limite como `RuntimeMaxSec=` só é opção se interromper o trabalho
  for seguro e a política o permitir; não o imponhas apenas para caber na janela.
- Se a fonte aprovada já tiver a configuração desejada e o host divergir,
  prepara a reconciliação autorizada. Confirma dependências antes de instalar
  apenas um `.timer` ou também o `.service`; o repositório não prova sozinho que
  a versão proposta pode ser instalada isoladamente.

## Ficheiro certo, daemon com o valor antigo

Se o ficheiro em disco está certo e o comportamento não mudou, o daemon pode
não o ter carregado, ou a versão instalada pode não suportar reload. Lê
[references/daemon-reload-and-runtime-state.md](references/daemon-reload-and-runtime-state.md),
que inclui o caso da política de energia num servidor em hardware de portátil.

## Antes de remover uma variável de um ficheiro

Confirma que a camada que fica fornece o valor que a aplicação efetivamente
consome. O ambiente de `/proc` sozinho não prova isso: prefere um diagnóstico
seguro e específico da aplicação, sem imprimir segredos. Não alteres o serviço
nem removas a variável sem autorização.

## Quando não aplicar

Num sistema com uma só fonte conhecida e sem divergência observada, este
procedimento é desnecessário. Usa-o quando houver evidência ou suspeita concreta
de que a configuração declarada difere da efetiva. Uma mudança de identidade,
por si só, não ativa esta Skill; pode ser contexto relevante se surgir um
sintoma compatível com essa divergência.
