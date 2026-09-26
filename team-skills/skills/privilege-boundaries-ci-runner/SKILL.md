---
name: privilege-boundaries-ci-runner
description: Separar identidades num servidor onde correm CI runners, agentes de IA e serviços de produção, e decidir que credenciais cada uma recebe. Usa quando um runner de CI vai correr na máquina de produção, quando se desenha quem pode fazer deploy, ou quando um script propõe copiar chaves SSH ou dar grupos a uma identidade.
---

# Fronteiras de privilégio

A pergunta certa não é "quem tem sudo", é **"se este processo for comprometido,
o que é que alcança?"**. Num servidor típico, a resposta é quase sempre "tudo",
por razões que não são óbvias.

## Root sem parecer root

Pertencer aos grupos `docker` ou `lxd` é equivalente a root: um contentor com
o disco do host montado dá acesso completo. Um sudoers estreito não é fronteira
nenhuma enquanto a mesma identidade tiver Docker.

```bash
getent group docker lxd
```

Isto aplica-se aos agentes de IA. Se o agente corre com o teu utilizador, tem
root efetivo, as tuas chaves SSH, os segredos dos serviços e os backups.
Reconhece-o explicitamente, ou separa-o. Não finjas que a password do sudo
resolve.

## Identidades mínimas para um host destes

| Identidade | Faz | Nunca recebe |
| --- | --- | --- |
| runner de CI | recebe o pedido de deploy | docker, lxd, segredos de serviço, credenciais de escrita |
| deploy | constrói releases e é dona delas | credencial de **escrita** em qualquer repositório |
| serviços | correm a aplicação | capacidade de escrever nas releases |
| backup | dump, restauro, cópias fora | acesso aos repositórios de código |
| humano/agentes | desenvolvimento | (decisão explícita; é aqui que mora o risco) |

Duas regras que valem mais do que parecem:

1. **A identidade que constrói nunca recebe credencial de escrita.** Instalar
   dependências executa código de terceiros. Com uma chave de escrita, uma
   dependência comprometida escreve no repositório que define a infraestrutura.
2. **Os serviços não podem escrever nas releases.** Se o serviço corre com a
   identidade dona da release, pode sempre mudar as permissões e reescrever o
   seu próprio código. Selar como `root:<grupo>` resolve, e continua a permitir
   construir a seguir, desde que o motor corra como root.

## O canal de deploy sem sudo

Num runner endurecido, `sudo` não funciona (`NoNewPrivileges`) e, mesmo que
funcionasse, `ProtectSystem=strict` impediria o trabalho. O padrão que
funciona:

1. O runner escreve um pedido (o SHA) num ficheiro dentro do seu próprio
   diretório gravável.
2. O runner pede `systemctl start deploy@<componente>.service` — por D-Bus, que
   não precisa de setuid e portanto convive com `NoNewPrivileges`.
3. Uma regra polkit autoriza **só** aquele utilizador, **só** o verbo `start`,
   **só** as instâncias de uma lista fechada.
4. A unit root lê o pedido com `O_NOFOLLOW` a partir de um descritor do
   diretório, exige dono, modo, tamanho e formato, e confirma que o SHA é o
   topo atual do branch remoto antes de fazer o que quer que seja.

O resultado: o runner não escolhe comandos, não passa argumentos, não corre
como root, e mantém o sandbox completo.

## Credenciais

- Chaves por repositório, de leitura, com alias SSH explícito por repositório.
  Nada de uma chave pessoal a servir tudo.
- Confirma se uma chave tem escrita antes de a copiar para outra identidade
  (`git push --dry-run` para um branch que nunca vais criar).
- Tokens de longa duração fora de homes acessíveis a runners e agentes. Se
  existir um temporário, tem data para morrer e alguém que a cumpra.
- Segredos em ficheiros root-owned fora dos checkouts, `0600`, carregados pela
  unit. Um `.env` dentro de um repositório é um acidente à espera.

## Topologia de chaves: a mesma chave em quatro sítios

Antes de mexer numa credencial, faz o **mapa** dela. Num host destes, a mesma
chave privada reaparece em sítios que ninguém enumera de cabeça. Caso real, uma
só chave de um repositório vivia em quatro lugares:

- `~/.ssh/` da conta humana (onde tu e os agentes empurram);
- `/var/lib/<serviço>/.ssh/` da identidade de serviço (o motor de deploys);
- `/etc/<projeto>/<orquestrador>-pull-ssh/` (os *pull steps* clonam com esta,
  em cada execução de flow);
- `/etc/<projeto>/<monitor>-ssh/` (um verificador de saúde).

Sonda, e compara por fingerprint em vez de por nome de ficheiro:

```bash
for f in ~/.ssh/*.pub; do printf '%-40s %s\n' "$f" "$(ssh-keygen -lf "$f" | awk '{print $2}')"; done
sudo sh -c 'for f in /var/lib/*/.ssh/* /etc/*/*ssh*/*.key; do
  printf "%-60s %s\n" "$f" "$(ssh-keygen -lf "$f" 2>/dev/null | awk "{print \$2}")"; done'
```

Nomes diferentes podem ser a mesma chave; nomes iguais podem ser chaves
diferentes. Só o fingerprint decide.

## Escrita concedida a ti é escrita concedida ao runtime

A consequência que mais custa, e que não se vê no painel do fornecedor: se a
chave é **partilhada** entre a tua conta e a identidade de serviço, ligar-lhe
escrita "temporariamente" para tu poderes publicar dá escrita **também** ao
serviço. E se essa identidade é a que corre os workers do orquestrador, então
código de um trabalho agendado pode empurrar para o ramo principal — o mesmo
ramo que o validador de deploys aceita como verdade para ativar releases. Toda a
revisão que construíste passa a ter uma porta ao lado.

O desenho correto, por repositório:

| Identidade | Chave | Permissão |
| --- | --- | --- |
| serviço que clona em runtime | própria | **só leitura** |
| humano e agentes | própria, separada | escrita |

E a sequência que não deixa janela sem escrita: adiciona primeiro a chave nova
de escrita, prova com `push --dry-run`, e **só depois** retira a escrita à
partilhada. Muitos fornecedores não deixam editar o modo de uma chave: obriga a
apagar e recriar, por isso obtém a pública **antes** de apagar, e faz os dois
passos seguidos — no intervalo, o runtime não clona.

Prova o resultado nos dois sentidos, com a identidade do serviço:

```bash
sudo -u SERVICO env GIT_SSH_COMMAND="/usr/bin/ssh -F /var/lib/SERVICO/.ssh/config -o BatchMode=yes" \
  git ls-remote REMOTO main            # tem de devolver o SHA
# e um push --dry-run a partir de um clone temporário: tem de ser recusado
```

## Apagar uma chave "duplicada" parte o runtime

Duas chaves de leitura no mesmo repositório parecem desarrumação e às vezes uma
delas é a do serviço. Apagar as duas deixa o sistema a funcionar — até ao
próximo clone. Num caso real, o serviço só voltou a precisar da chave onze horas
depois, e o que rebentou foi um deploy; e o serviço com o worker vivo **não podia
ser reiniciado**, porque o arranque dele valida o acesso ao repositório.

Antes de apagar qualquer credencial: mapeia por fingerprint, identifica de quem
é cada uma, e guarda a pública. Se a privada existir no host e a pública não,
`ssh-keygen -y -f privada` recupera-a — apagar o registo remoto não destrói nada
localmente.

## Sequência segura para apertar isto

1. Criar as identidades (não muda nada).
2. Mover os segredos para fora das homes.
3. Mudar os serviços de identidade, um de cada vez, com rollback.
4. Substituir o runner por um isolado e provar um deploy real pelo canal novo.
5. Só então retirar credenciais e grupos temporários, e confirmar que foram
   retirados.

## Templates

Para montar este canal, consulta
[references/release-request-contract.md](references/release-request-contract.md).
As units, a regra polkit, o cliente e o validador têm de ser implementados e
testados no repositório que governa o host; este catálogo não os instala.

## Quando não aplicar

Se ninguém além de ti toca na máquina e não há automação a correr código de
fora, a separação de identidades tem pouco retorno. A partir do momento em que
há um runner ou um agente, tem.
