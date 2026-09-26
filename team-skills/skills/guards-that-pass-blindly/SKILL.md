---
name: guards-that-pass-blindly
description: Rever scanners de segurança ou gates em que um `PASS` pode ocultar inputs obrigatórios não lidos ou não analisados, zero valores extraídos quando eram esperados, ou deteção incompleta de segredos. Não para health checks comuns nem validadores sem esse risco específico.
---

# Um guarda que não vê passa sempre

O código de um guarda descreve uma intenção. O que interessa é o que ele
consegue **ler** na máquina onde corre. Entre as duas coisas cabe a falha mais
perigosa deste tipo de sistema: a verificação que devolve `PASS` porque não
conseguiu abrir nada.

Exemplo ilustrativo de um scanner de segredos que comparava blobs de um
repositório com valores de referência protegidos:

```python
try:
    lines = path.read_text().splitlines()
except (FileNotFoundError, PermissionError, IsADirectoryError):
    continue        # <-- aqui morre a verificação, em silêncio
```

Neste cenário, o serviço corria com uma identidade sem acesso aos ficheiros
obrigatórios. A lista de valores comparáveis ficava **vazia**, mas o scanner
reportava que não encontrou segredos.

## As três perguntas

**1. Que runtime executa o guarda, com que identidade e quais inputs são
obrigatórios?** Confirma a configuração e o contrato do próprio guarda antes de
interpretar permissões. Só uses comandos systemd se o alvo for Linux e o
serviço for realmente gerido por systemd; noutros runtimes, identifica as
interfaces e evidências equivalentes.

```bash
systemctl show UNIT -p User -p Group --value
id IDENTIDADE
stat -c '%a %U:%G %n' INPUT_PATH
```

Repete `stat` apenas para inputs relevantes, enumerados a partir do manifesto do
guarda sem word-splitting ou globs que percam caminhos com espaços. Um modo
`0600` de outro dono pode impedir a leitura, mas confirma a identidade, ACLs,
mounts e runtime efetivos.

**2. Que inputs e resultados exige o contrato do guarda?** Exige evidência
proporcional ao contrato, como contagens de inputs obrigatórios lidos e
resultados analisados. Um `PASS` não deve esconder inputs obrigatórios em falta
ou ilegíveis. Distingue-os dos opcionais, que devem aparecer explicitamente
como opcionais/ignorados. Uma contagem de valores extraídos só é obrigatória
quando o contrato prevê um mínimo; documenta quando zero resultados é válido.

**3. O que acontece quando um input obrigatório falta ou não abre?** O guarda
deve reportar a condição e não apresentar um `PASS` como se a verificação
estivesse completa. Um input opcional pode ser omitido se essa possibilidade
estiver declarada no contrato e no resultado. Um `continue` silencioso num
`except PermissionError` oculta a diferença.

## Distingue zero valores de falha de leitura

Um ficheiro que abre e produz zero valores pode estar vazio legitimamente ou
ter um formato que o parser não reconhece. Distingue esses resultados segundo o
contrato do input; não trates todo zero como ilegível nem como falha.

Isto apanha uma classe inteira de erros de parser: um ficheiro de **valor nu**
sem `chave=`, um `.ini` com secções, um ficheiro de autenticação de proxy, uma
configuração de cliente de armazenamento. Cada formato precisa do parser
adequado e de um resultado que permita distinguir sucesso vazio, dados
analisados e formato inválido. Exige pelo menos um valor apenas quando o
contrato desse input o requer.

## Deteção por nome é uma lista negra que perde sempre

Uma regra como `(?:TOKEN|SECRET|PASSWORD|API_KEY|DATABASE_URL|DSN)$` parece
razoável e pode falhar no primeiro nome que alguém inventar. Exemplos de nomes
que uma regra por sufixo pode não abranger:

- `PREFECT_API_DATABASE_CONNECTION_URL` — termina em `CONNECTION_URL`
- `DATA_OPS_ALERT_WEBHOOK_URL` — termina em `WEBHOOK_URL`

Para um scanner baseado em chaves, uma política explícita de classificação pode
ser adequada. Aplica-a apenas aos formatos, inputs e garantias de cobertura que
o scanner suporta; define o tratamento de chaves desconhecidas no contrato, em
vez de assumir que todo guarda precisa de classificar todas as chaves.

## Quando o guarda não pode ler, não baixes as permissões

A tentação é dar ao guarda acesso ao que lhe falta — meter a identidade num
grupo, abrir um `0600` para o grupo. Isso resolve a verificação e alarga a
superfície. Alternativas, por ordem de preferência:

1. **Uma fase privilegiada separada** que lê o que é preciso e emite um
   **veredicto** assinado pelo contexto: intervalo, hashes dos próprios
   verificadores, hora, resultado. A parte sem privilégios exige o veredicto e
   recusa se faltar, estiver expirado, ou pertencer a outro intervalo.
2. **Comparação por digest** — só se o que procuras tem fronteiras conhecidas.
   Não serve para procurar um segredo como substring de um ficheiro arbitrário:
   para isso precisarias de enumerar candidatos ou de dar ao processo material
   equivalente ao próprio segredo.
3. Alargar o acesso — último recurso, e com o custo escrito.

Se o alvo for Linux/systemd, confirma na versão instalada a semântica de
`ExecStartPre=`, `ExecStartPost=` e dos prefixos de privilégio antes de propor
esse desenho. A verificação que autoriza uma ação irreversível tem de ocorrer
antes dessa ação, por exemplo num precheck apropriado seguido do comando
protegido. `ExecStartPost=` corre depois de `ExecStart=` e não pode autorizar
nem impedir retroativamente uma ação já executada; só pode condicionar passos
posteriores que dependam do resultado da unit. Este desenho não se aplica
automaticamente a outros runtimes.

## Recolhe evidência do privilégio e da leitura

Não aprove um desenho destes por doutrina. Faz o guarda **imprimir** o que
provaria a dúvida, e exige essa linha no journal:

```
source_secret_phase=pre euid=0 probe=1
source_secret_probe phase=pre required_inputs=<count> analyzed_values=<count> verdict_write=PASS
```

Se o alvo usar Linux/systemd e essa evidência for necessária, uma unit de prova
transitória em `/run/systemd/system` pode testar parte das diretivas de sandbox.
Só a cries com autorização e um plano de limpeza. O resultado é evidência, não
prova automática de equivalência: antes de extrapolar para produção, confirma
runtime, identidade, inputs, mounts, versões e restantes condições efetivas.
Noutros runtimes, usa o mecanismo de prova equivalente.

Duas considerações específicas dessa unit:

- sem `RemainAfterExit=yes`, uma unit transitória que ninguém referencia é
  **descarregada** ao ficar inativa, e o `InvocationID` desaparece — o
  `systemctl show` seguinte devolve vazio. Units normais mantêm-no porque um
  timer as referencia.
- a ordem tem de ser: arrancar, ler o `InvocationID`, verificar o journal
  dessa invocação, **parar**, remover o ficheiro, `daemon-reload`.

## Exceções para scanners de objetos versionados

Para scanners que reveem objetos versionados com identificadores, caminhos e
fingerprints estáveis, uma exceção pode ser presa aos atributos que identificam
aquele achado. Não uses este mecanismo como regra geral para outros tipos de
guardas. Evita allowlists permanentes por caminho; quando aplicável, associa a
exceção a:

- o **ponto de partida** exato (cursor, base, versão) — e torna-se inerte
  quando ele avança;
- os **identificadores exatos** dos objetos, não os caminhos;
- o caminho esperado **de cada** objeto;
- o **multiconjunto** dos fingerprints das ocorrências: contagens iguais, não
  apenas o conjunto, para que uma ocorrência extra ou repetida volte a bloquear;
- apenas a **regra** que foi revista; as outras continuam a correr sobre os
  mesmos objetos.

Assim a exceção descreve um facto histórico e não uma permissão futura.

## Sinais de alarme

- `except PermissionError: continue` em código de verificação.
- Um `PASS` sem contagem de inputs.
- Um guarda que nunca disse NÃO desde que foi instalado.
- Uma allowlist por caminho, ficheiro ou identidade.
- Uma regra de deteção construída com sufixos de nomes.
- Uma etapa privilegiada cujo privilégio ninguém demonstrou.

## Quando não aplicar

Num guarda que corre como root, com um só input, e cuja falha é ruidosa, isto é
excesso. O peso justifica-se quando o guarda corre com identidade reduzida,
tem vários inputs de formatos diferentes, ou é a última coisa entre um segredo
e um sítio de onde não se apaga.

## Relacionadas

- `verify-against-the-host`: como rever o que um agente afirma.
- `host-mutation-batches`: onde um lote prova as suas próprias verificações.
- `privilege-boundaries-ci-runner`: quem pode ler o quê, e porquê.
