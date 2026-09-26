---
name: guards-that-pass-blindly
description: Verificar que uma verificação de segurança consegue mesmo ver o que diz verificar. Usa ao rever scanners de segredos, validadores, gates, health checks e qualquer guarda cujo resultado seja PASS; quando um PASS parece bom demais; quando uma regra de deteção depende de nomes; ou antes de confiar num guarda que nunca disse NÃO.
---

# Um guarda que não vê passa sempre

O código de um guarda descreve uma intenção. O que interessa é o que ele
consegue **ler** na máquina onde corre. Entre as duas coisas cabe a falha mais
perigosa deste tipo de sistema: a verificação que devolve `PASS` porque não
conseguiu abrir nada.

Caso real, num scanner de segredos que comparava cada blob de um repositório
com os segredos verdadeiros do host:

```python
try:
    lines = path.read_text().splitlines()
except (FileNotFoundError, PermissionError, IsADirectoryError):
    continue        # <-- aqui morre a verificação, em silêncio
```

O serviço corria como uma identidade de backup. Os cinco ficheiros de segredos
configurados eram todos `0600`, de `root` ou de outro utilizador. Resultado: a
lista de segredos a comparar ficava **vazia**, e o scanner reportava que não
encontrou nenhum segredo — o que era verdade e não significava nada.

## As três perguntas

**1. Com que identidade corre, e consegue ler os inputs?**

```bash
systemctl show UNIT -p User -p Group --value
id IDENTIDADE
for f in $(lista de inputs); do stat -c '%a %U:%G %n' "$f"; done
```

Modo `0600` de outro dono significa zero. Não presumas que um serviço "do
sistema" lê ficheiros do sistema.

**2. Quantos inputs viu, e quantos valores extraiu?** Um guarda tem de
publicar essa contagem, e quem revê tem de a exigir. `PASS` sem denominador
não é resultado. No caso real, a correção fez o guarda imprimir
`inputs=31 comparable_values=37` — e é isso que se lê primeiro, antes do `PASS`.

**3. O que acontece quando um input falta ou não abre?** A única resposta
aceitável é **falhar**. Um `continue` num `except PermissionError` transforma
uma verificação em decoração.

## Corolário: um input que produz zero valores é um input ilegível

Se um ficheiro abre mas o extrator não tira nada dele — formato diferente,
chave com outro nome, comentários — o efeito é idêntico a não o ter lido.
Trata os dois casos da mesma maneira: falha, com o caminho no erro.

Isto apanha uma classe inteira de erros de parser: um ficheiro de **valor nu**
sem `chave=`, um `.ini` com secções, um ficheiro de autenticação de proxy, uma
configuração de cliente de armazenamento. Cada formato precisa do seu parser, e
cada parser precisa de prova de que devolveu pelo menos um valor.

## Deteção por nome é uma lista negra que perde sempre

Uma regra como `(?:TOKEN|SECRET|PASSWORD|API_KEY|DATABASE_URL|DSN)$` parece
razoável e falha em silêncio no primeiro nome que alguém inventar. Casos reais
que escaparam a essa regra exata:

- `PREFECT_API_DATABASE_CONNECTION_URL` — termina em `CONNECTION_URL`
- `DATA_OPS_ALERT_WEBHOOK_URL` — termina em `WEBHOOK_URL`

Inverte: **classifica explicitamente cada chave de cada input** como segredo ou
público, e **falha quando aparece uma chave sem classificação**. A regra por
sufixo passa a ser conveniência, não defesa. O custo é um ficheiro de política
para manter; o retorno é que um segredo novo não pode entrar sem alguém decidir
o que ele é.

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

No systemd, o prefixo `!` num `ExecStartPre=`/`ExecStartPost=` corre essa etapa
como root **mantendo** o sandbox da unit. E, em `Type=oneshot`, o
`ExecStartPost=` não corre se o `ExecStart=` falhar — o que é exatamente o que
torna seguro um desenho onde a fase final privilegiada é a única que autoriza o
passo irreversível.

## Prova que o privilégio e a leitura acontecem de facto

Não aprove um desenho destes por doutrina. Faz o guarda **imprimir** o que
provaria a dúvida, e exige essa linha no journal:

```
source_secret_phase=pre euid=0 probe=1
source_secret_probe phase=pre inputs=31 comparable_values=37 verdict_write=PASS
```

Melhor ainda: uma **unit de prova transitória**, em `/run/systemd/system`, com
as mesmas diretivas de sandbox da unit de produção e `ReadWritePaths` mais
estreito, arrancada e removida pelo próprio lote antes de instalar nada.
Se o PASS acontece ali, acontece em produção.

Duas armadilhas dessa unit, ambas encontradas na prática:

- sem `RemainAfterExit=yes`, uma unit transitória que ninguém referencia é
  **descarregada** ao ficar inativa, e o `InvocationID` desaparece — o
  `systemctl show` seguinte devolve vazio. Units normais mantêm-no porque um
  timer as referencia.
- a ordem tem de ser: arrancar, ler o `InvocationID`, verificar o journal
  dessa invocação, **parar**, remover o ficheiro, `daemon-reload`.

## Um achado revisto deixa-se passar uma vez, nunca por caminho

Quando um guarda bloqueia algo que já foi revisto e considerado inofensivo, a
tentação é pôr o caminho numa allowlist. Isso cega aquele caminho para sempre.
A exceção correta é presa a **tudo** o que a identifica:

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
