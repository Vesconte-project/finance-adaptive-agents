---
name: effective-config-tracing
description: Descobrir de onde vem realmente o valor que um serviço usa, quando o ficheiro do repositório diz uma coisa e o processo faz outra. Usa quando um serviço usa um caminho, credencial ou parâmetro que ninguém encontra no código, quando uma alteração de configuração não produz efeito, quando um serviço parte depois de mudar de identidade, ou antes de remover uma variável de um ficheiro por assumires que é a fonte.
---

# Onde é que este valor nasce, afinal

A pergunta que resolve incidentes não é "o que diz a configuração", é **"que
valor tem este processo, neste momento, e quem o pôs lá"**. São coisas
diferentes, e a distância entre elas cresce com a idade do sistema.

## As camadas, pela ordem em que ganham

Num serviço systemd típico, o valor efetivo vem da última camada que o define:

1. omissão no código da aplicação;
2. `Environment=` na unit;
3. cada `EnvironmentFile=` **pela ordem em que aparece** — o último ganha;
4. drop-ins em `<unit>.d/*.conf`, que podem acrescentar mais ficheiros;
5. o que o processo-pai injeta ao lançar o filho;
6. **valores guardados noutro sistema** — uma base de dados de orquestração,
   um registo de tarefas, uma configuração de deployment — que se sobrepõem a
   tudo o que está no host.

A camada 6 é a que se esquece, e é a que mais custa. Já vi um caminho errado
viver durante meses numa tabela de um orquestrador, enquanto toda a gente lia
e corrigia ficheiros no host que não estavam a ser usados.

## O método

**1. Começa pelo processo, não pelo repositório.**

```bash
pid=$(systemctl show UNIT -p MainPID --value)
sudo sh -c "tr '\0' '\n' < /proc/$pid/environ" | cut -d= -f1 | sort   # só nomes
```

O `sudo` tem de envolver o redireccionamento (`sh -c '... < ficheiro'`); caso
contrário é o teu shell, sem privilégios, a tentar abrir o ficheiro.

**2. Lista as camadas declaradas e a sua ordem.**

```bash
systemctl cat UNIT | grep -nE '^(Environment=|EnvironmentFile=)'
ls /etc/systemd/system/UNIT.d/ 2>/dev/null
```

Um drop-in antigo pode repor um ficheiro que já ninguém esperava. Verifica
sempre se existe.

**3. Procura a camada que não vive no host.** Se há um orquestrador, um
agendador ou um serviço que lança o teu processo, pergunta o que ele injeta:

```bash
# exemplo: definições de deployment guardadas na base do orquestrador
curl -s -X POST http://127.0.0.1:PORTA/api/deployments/filter \
  -H 'content-type: application/json' -d '{"limit":200}' \
  | python3 -c "import json,sys; [print(d['name'], sorted((d.get('job_variables') or {}).get('env',{}))) for d in json.load(sys.stdin)]"
```

Imprime **nomes de chaves**, nunca valores: estas camadas costumam guardar
credenciais.

**4. Confirma a hipótese com uma experiência barata.** Reproduz o acesso com a
identidade e o caminho reais antes de mudar código:

```bash
sudo -u IDENTIDADE test -w /caminho && echo ok || echo "sem escrita"
sudo -u IDENTIDADE test -x /caminho/pai && echo "atravessa" || echo "não atravessa"
```

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
- **A ordem dos `EnvironmentFile=` não é evidente na leitura.** Escreve-a no
  documento do serviço, ou remove a duplicação.

## Antes de remover uma variável de um ficheiro

Confirma que a camada que fica **a fornece mesmo**. A remoção parece segura
porque "o outro sítio também a tem" — e é assim que se parte um serviço
inteiro. Verifica no processo em execução, com o comando do passo 1.

## Quando não aplicar

Num sistema com uma só fonte de configuração, e onde o processo corre com a
identidade de quem escreveu os ficheiros, isto é excesso. O método ganha valor
quando há várias camadas, identidades diferentes, ou um orquestrador pelo meio.
