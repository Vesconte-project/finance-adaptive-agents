---
name: effective-config-tracing
description: Rastrear uma divergência entre a configuração declarada e a configuração efetiva de um serviço, incluindo alterações ineficazes ou problemas de acesso após mudar a identidade. Usa quando há evidência dessa divergência; não para erros de parsing ou falhas sem discrepância de configuração.
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
pid=$(systemctl show UNIT -p MainPID --value)
sudo sh -c "tr '\0' '\n' < /proc/$pid/environ" | cut -d= -f1 | sort
```

Este comando imprime nomes de variáveis presentes no ambiente inicial do
processo, não valores efetivos nem as respetivas fontes. A aplicação pode
transformá-los, removê-los ou carregar configuração adicional; não uses esta
sonda isoladamente para concluir qual é o valor que ela consome. Usa `sudo`
apenas se estiver autorizado. O redireccionamento dentro de `sh -c` permite
que a leitura seja feita com os privilégios aprovados.

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
  por acaso até alguém mudar a ordem ou remover o sítio errado. Deixa um só.
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
