---
name: immutable-deploys-single-host
description: Desenhar releases imutáveis para serviços num único host Linux que atualmente correm a partir de checkouts Git mutáveis. Usa para substituir esse modelo por releases fixadas e verificáveis; não para rollback genérico, Kubernetes ou para definir um componente sem esse contexto.
---

# Releases imutáveis num host único

O objetivo não é sofisticação: é poder responder a "o que está a correr?" e a
"como volto atrás?" sem interpretar o estado de um checkout mutável.

## O modelo

O layout abaixo é apenas um exemplo para um host Linux. Primeiro confirma a
plataforma, os caminhos existentes, proprietários, mounts e permissões
autorizadas; escolhe destinos compatíveis com o serviço e a política local:

```text
/srv/PROJ/releases/<componente>/<commit-id>/  exemplo de release
/srv/PROJ/current/<componente> -> uma release
/srv/PROJ/state/                             exemplo de estado externo
/srv/PROJ/artifacts/                         exemplo de artefactos externos
/var/lib/<deploy>/releases/<componente>.json exemplo de receipt
```

Quando a plataforma e o gestor de serviços suportarem symlinks, um serviço pode
apontar para `current/<componente>/...`; a troca atómica depende de paths no
mesmo filesystem e de permissões confirmadas.

## Componente, não repositório

Um componente é a unidade que se implanta e se reverte. Um repositório pode
dar vários componentes (uma API, um worker, um job agendado) e um componente
pode juntar vários repositórios (um runtime composto, fixado por um
`runtime-lock.json` no repositório principal).

Cada componente declara, conforme aplicável: origem e SHA, tipo de build,
serviços e timers, identidade de runtime, readiness, estado, dependências e
política de rollback. Guarda a configuração segundo o modelo de privilégio
verificado; root-owned é uma opção apenas quando a plataforma e a política local
o exigirem. O código da aplicação não deve depender de caminhos específicos do
host sem uma interface de configuração explícita.

## Construir

1. Buscar o commit escolhido pela identidade e credencial autorizadas para o
  workflow.
2. Validar o SHA conforme a política de promoção: exigir o topo do branch pode
  ser adequado a deploys sequenciais desse branch; SHAs fixados, releases
  anteriores ou branches de release podem ser intencionais. Regista a política
  e valida o SHA contra ela.
3. Construir num staging adequado à plataforma e ao modelo de confiança, usando
  lockfiles e instalação não editável quando suportados pelo projeto.
4. Testar importações e execução com a identidade de runtime, se o serviço
  permitir esse teste sem efeitos secundários.
5. Renomear para o nome definitivo e escrever `RELEASE.json` com repositório,
   SHA, extras, versão do interpretador, hash do contrato e data.
6. Aplicar propriedade e modos segundo o modelo de privilégio verificado; não
  assumes root, um grupo específico ou estes modos sem validar a política do
  host.

## Selar e verificar integridade

Depois de finalizar uma release, calcula um manifesto de integridade do
conteúdo imutável (por exemplo, caminhos relativos e hashes), ligado ao commit
e à proveniência do build. Guarda o manifesto num local protegido pela política
do host. Aplica os controlos de acesso disponíveis para impedir que identidades
de runtime ou automação de menor confiança alterem a release; root, filesystem
read-only, ACL ou outro mecanismo são escolhas locais, não requisitos fixos.

Após a ativação, verifica o conteúdo contra esse manifesto confiável e confirma
que o processo usa o alvo esperado antes de marcar a release como `verified`.
Se o host não conseguir impedir alterações, descreve a verificação como
detetiva e declara esse limite; não assumes imutabilidade apenas pelo nome do
diretório ou pelos modos configurados.

Dois exemplos a verificar no runtime escolhido: console scripts de uma venv
podem guardar o caminho de staging no shebang, e a aplicação pode precisar de
escrever fora do pacote. Testa o launcher no caminho final e define um destino
de escrita autorizado se esse requisito existir.

## Ativar

Confirma primeiro o gestor de serviços, o alvo, as dependências, a janela e as
permissões efetivas. Só executa a ativação quando o operador e o workflow
autorizarem a operação. Se usar systemd, planeia e verifica apenas as units
necessárias; noutro runtime, usa o procedimento correspondente. Troca o alvo,
arranca e **prova** readiness antes de gravar `verified`. Em falha, repõe o alvo
anterior apenas se a recuperação for segura, verificada e autorizada; regista o
resultado real sem declarar sucesso só porque o caminho foi restaurado.

## Readiness que vale alguma coisa

A regra: **nunca aceitar como prova um estado que já era verdade antes da
mudança**.

- HTTP: se existir um endpoint versionado e o teste estiver autorizado, verifica
  a versão nova em vez de confiar apenas num `/health` genérico.
- Workers com heartbeat: se aplicável, exige heartbeat **posterior** ao início
  da ativação.
- Processo: quando o runtime permitir, confirma `cwd`, executável e `PATH`
  efetivos sem expor dados sensíveis.
- Interface pública: se existir e o operador autorizar o teste, verifica o
  resultado; não contactes destinos externos por defeito.

## Código que não vive na release

Se o sistema clona o código no momento da execução (workers de orquestração,
por exemplo), a release governa o ambiente, não o código executado. Nesse
caso, publicar as definições fixadas ao SHA da release faz parte da ativação,
e tem de ser verificado depois. Caso contrário o `current/` mente.

## Retenção

Define retenção segundo requisitos de capacidade, auditoria e recuperação do
serviço. Limpeza é uma operação separada, com inventário e autorização; não
apagues a única cópia recuperável nem assumas um número fixo de releases.

## Referência de contrato

Para definir contrato, unit e caminhos de estado, consulta
[references/component-contract.md](references/component-contract.md). Os
ficheiros instaláveis pertencem ao repositório que governa o host.

## Quando não aplicar

Um serviço sem estado, que se recria num minuto, não precisa disto. O valor
aparece quando há dados, dependências entre serviços, e mais do que uma
pessoa ou agente a mexer.
