---
name: immutable-deploys-single-host
description: Desenhar deploys por releases imutáveis num único servidor, com symlink current, receipts, readiness real e rollback por componente, sem Kubernetes nem plataformas pesadas. Usa quando um host corre serviços a partir de checkouts Git mutáveis, quando é preciso rollback fiável, ou quando se define o que é um componente a implantar.
---

# Releases imutáveis num host único

O objetivo não é sofisticação: é poder responder a "o que está a correr?" e a
"como volto atrás?" sem interpretar o estado de um checkout mutável.

## O modelo

```
/srv/PROJ/releases/<componente>/<sha-40>/    imutável, read-only
/srv/PROJ/current/<componente> -> uma release
/srv/PROJ/state/                             estado, nunca dentro da release
/srv/PROJ/artifacts/                         artefactos, nunca dentro da release
/var/lib/<deploy>/releases/<componente>.json receipt da ativação
```

A unit systemd aponta **sempre** para `current/<componente>/...`. Trocar de
versão é trocar um symlink, atomicamente.

## Componente, não repositório

Um componente é a unidade que se implanta e se reverte. Um repositório pode
dar vários componentes (uma API, um worker, um job agendado) e um componente
pode juntar vários repositórios (um runtime composto, fixado por um
`runtime-lock.json` no repositório principal).

Cada componente declara: origem e SHA, tipo de build, units e timers,
identidade de runtime, readiness, estado que usa, dependências, política de
rollback. A configuração vive num ficheiro root-owned na máquina; o código da
aplicação não conhece caminhos do host.

## Construir

1. Buscar o commit exato, como a identidade de deploy, com chave **de leitura**.
2. Recusar um SHA que não seja o topo atual do branch (evita deploys fora de ordem).
3. Construir num diretório de staging, a partir de um lockfile commitado
   (`uv sync --frozen` ou equivalente), sem instalação editável.
4. Testar importações a partir do caminho final, com a identidade que o
   serviço vai usar.
5. Renomear para o nome definitivo e escrever `RELEASE.json` com repositório,
   SHA, extras, versão do interpretador, hash do contrato e data.
6. Selar: `root:<grupo-de-deploy>`, diretórios `0550`, ficheiros `0440`.

Duas armadilhas comprovadas: os console scripts da venv guardam o caminho de
staging no shebang (tens de os reescrever depois do rename), e a aplicação
pode querer escrever dentro do próprio pacote (aponta isso para o estado).

## Ativar

Parar as units, trocar o symlink, arrancar, **provar** que está pronto, e só
então gravar o receipt como `verified`. Em falha, repor o alvo anterior,
arrancar e verificar outra vez; o receipt fica `failed-rolled-back`.

Se o serviço tiver dependentes (`Requires=`), regista quais estavam ativos
antes do stop e arranca-os depois — o start não os repõe sozinho.

## Readiness que vale alguma coisa

A regra: **nunca aceitar como prova um estado que já era verdade antes da
mudança**.

- HTTP: código 200 num endpoint que só existe na versão nova é uma prova
  melhor do que um `/health` genérico.
- Workers com heartbeat: exigir heartbeat **posterior** ao início da ativação.
- Processo: confirmar `cwd` e executável dentro da release, e o `PATH` sem
  caminhos mutáveis.
- O que o utilizador usa: se há um dashboard ou endpoint público, testa-o.

## Código que não vive na release

Se o sistema clona o código no momento da execução (workers de orquestração,
por exemplo), a release governa o ambiente, não o código executado. Nesse
caso, publicar as definições fixadas ao SHA da release faz parte da ativação,
e tem de ser verificado depois. Caso contrário o `current/` mente.

## Retenção

Manter a atual e pelo menos duas anteriores. Limpeza é uma operação separada,
com inventário e confirmação. Cópias manuais feitas durante a iteração não são
releases: ou são apagadas, ou a auditoria passa a exigir que só existam
diretórios com nome de SHA.

## Templates

Para definir contrato, unit e caminhos de estado, consulta
[references/component-contract.md](references/component-contract.md). Os
ficheiros instaláveis pertencem ao repositório que governa o host.

## Quando não aplicar

Um serviço sem estado, que se recria num minuto, não precisa disto. O valor
aparece quando há dados, dependências entre serviços, e mais do que uma
pessoa ou agente a mexer.
