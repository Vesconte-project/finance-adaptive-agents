---
name: greenfield-host-setup
description: Planear a instalação inicial de um servidor com dados, deploys automáticos e agentes. Usa antes de instalar os primeiros serviços para decidir identidades, caminhos de estado, segredos, backups e CI e reduzir migrações posteriores.
---

# Dia 1 de um servidor que vai importar

Quase tudo o que custa caro num servidor é barato no primeiro dia e caro a
partir do segundo. Esta skill é a ordem que evita as migrações.

Cada passo traz o **custo de o saltar**, medido numa migração real de um
servidor que foi montado sem isto.

## 0. Decide o que esta máquina é

Se é descartável e se recria com um comando, pára de ler. Aplica só o passo 5
(backups) se houver dados. O resto é peso morto.

Se tem dados que te custam, ou vai receber deploys automáticos, ou vai ter
agentes a escrever código nela, continua.

## 1. Identidades antes de serviços

Cria, antes de instalar qualquer serviço:

- `<proj>-deploy`: constrói e é dona das releases. Shell `nologin`.
- `<proj>-svc`: corre os serviços (ou uma por domínio, se quiseres isolar).
- `<proj>-runner`: o runner de CI, sem grupos suplementares.
- `<proj>-backup`: backups e restauro.

Nenhuma delas em `docker` nem `lxd`, com uma exceção consciente e registada
se o backup precisar do contentor da base de dados.

O teu utilizador humano fica com `sudo`. Decide **agora**, por escrito, se os
agentes de IA correm com ele. Se sim, aceita que têm root efetivo e acesso a
tudo; se não, dá-lhes identidade própria desde o início.

> **Custo de saltar:** trocar a identidade de serviços já em produção obriga a
> mover segredos, reinstalar units, tratar dependências entre elas e testar
> tudo outra vez. Foi um lote inteiro, com três tentativas falhadas.

## 2. Declara os caminhos antes de existir estado

```
/srv/<proj>/releases/   código imutável
/srv/<proj>/current/    symlinks
/srv/<proj>/state/      tudo o que muda e importa
/srv/<proj>/artifacts/  resultados grandes
/etc/<proj>/paths.env   root-owned, 0644, só caminhos
/etc/<proj>/*.env       root-owned, 0600, segredos
```

A aplicação lê **nomes de variáveis**, nunca caminhos do host. Nenhum serviço
escreve dentro do diretório do código, nem nas releases.

> **Custo de saltar:** mover 17 GB de base de dados e 4 GB de artefactos que
> tinham ido parar dentro dos repositórios. Foi a parte mais lenta e a única
> verdadeiramente irreversível de toda a migração.

## 3. O primeiro serviço já corre de uma release

Mesmo que só tenhas um serviço, monta-o assim desde o início: release com
nome do SHA, construída a partir de um lockfile commitado, selada como
`root:<grupo-deploy>`, e a unit a apontar para `current/<componente>`.

É meia hora no dia 1. Ver `immutable-deploys-single-host`.

> **Custo de saltar:** com serviços a correr de checkouts, não há rollback e
> qualquer deploy arrisca os dados que lá estão ao lado.

## 4. O canal de deploy antes do primeiro deploy automático

O runner corre com a sua identidade, endurecido, e **não** usa `sudo`. Pede
por D-Bus (`systemctl start deploy@<componente>.service`), autorizado por
polkit só para aquele utilizador, aquele verbo e uma lista fechada de
instâncias. A unit root valida o pedido e confirma que o SHA é o topo atual
do branch antes de agir.

O workflow de deploy depende do CI verde (`workflow_run` com
`conclusion == 'success'` e `event == 'push'`), não de um push qualquer.

> **Custo de saltar:** um runner com o teu utilizador dá root a qualquer
> commit em `main`. Tentar endurecê-lo depois esbarra em `NoNewPrivileges` e
> `ProtectSystem`, que partem o `sudo` e o próprio motor de deploy.

## 5. Backups e restauro no mesmo dia dos dados

- Dump automático, verificado, copiado para fora da máquina.
- **Teste de restauro** agendado, para uma base isolada. Um backup sem
  restauro testado é uma suposição.
- Cópia para fora **também** dos artefactos, do estado das ferramentas e dos
  segredos (estes cifrados, com chave que só tu tens).
- Os programas de backup correm de cópias instaladas root-owned, nunca de um
  checkout.

> **Custo de saltar:** numa migração observada, só a base de dados tinha cópia
> externa; artefactos, estado do registry e segredos existiam num sítio só.

## 6. Um caminho de reconstrução, desde o início

Um script idempotente que, numa máquina vazia, cria identidades, diretórios,
runtimes, motor, units, restaura o estado e deixa tudo a correr. Escreve-o
enquanto montas o servidor: é literalmente o que estás a fazer à mão.

Ensaia-o uma vez numa máquina descartável e mede quanto tempo demora e o que
se perde.

> **Custo de saltar:** sem ele, "recriar o servidor" são dias de trabalho
> manual com passos que ninguém escreveu, descobertos sob pressão.

## 7. Schema separado do código, desde a primeira migração

Quem é dono de um schema expõe `plan`, `apply`, `verify` e `version`. Cada
release declara a versão mínima e máxima de schema que suporta, e o motor
recusa uma release incompatível. Migrações correm como operação própria, com
backup fresco, nunca no meio de um deploy.

> **Custo de saltar:** um deploy de código pode introduzir incompatibilidade
> em silêncio, e o rollback de código não desfaz uma migração de dados.

## 8. Só depois, conveniências

Dashboards, túneis, ferramentas de ficheiros, agentes. Cada uma com a sua
identidade e o seu estado declarado, pelas mesmas regras.

## Verificação do dia 1

Antes de dizeres que está pronto, prova cada uma destas:

- [ ] Nenhum serviço corre de um diretório onde alguém edita código.
- [ ] `getent group docker lxd` não tem lá o runner nem os serviços.
- [ ] Um deploy completo correu pelo canal automático, do push ao serviço vivo.
- [ ] Um rollback correu, provocado de propósito.
- [ ] Um restauro correu, a partir da cópia que está fora da máquina.
- [ ] `grep -r /home /etc/<proj>/*.env` não devolve nada.
- [ ] Existe um script que reconstrói isto numa máquina vazia, e já correu.

Enquanto faltar uma destas, o servidor está no estado em que este esteve: a
funcionar, mas a acumular trabalho para depois.
