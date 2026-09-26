---
name: privilege-boundaries-ci-runner
description: Rever fronteiras de privilégio quando um runner CI, agente ou automação influenciável partilha um host de produção ou credenciais de produção com serviços/deploys. Usa para separar essas identidades e limitar o canal de deploy; não para desenho genérico de deploys ou gestão de chaves SSH isolada.
---

# Fronteiras de privilégio

A pergunta certa não é apenas "quem tem sudo", é **"se este processo for
comprometido, que recursos consegue alcançar com as permissões efetivas?"**. A
resposta depende da configuração verificada no host, dos serviços e das
credenciais disponíveis; não a infiras de um rótulo ou grupo isolado.

## Root sem parecer root

Pertencer a grupos como `docker` ou `lxd` pode permitir controlo equivalente a
root quando o daemon, a configuração e os mounts permitem acesso ao host. A
membership, por si só, não prova esse acesso: confirma o modo do daemon,
restrições e controlos efetivos antes de concluir.

```bash
getent group docker lxd
```

Este exemplo só se aplica se o host for Linux e tiver `getent`; valida a
configuração real do daemon e dos mounts antes de inferir capacidades.

Em agentes e runners, verifica as credenciais, grupos e recursos realmente
acessíveis à identidade. Não infiras root efetivo nem acesso a chaves, segredos
ou backups apenas pelo nome de utilizador ou pela existência de sudo.

## Identidades mínimas para um host destes

| Identidade | Faz | Nunca recebe |
| --- | --- | --- |
| runner de CI | recebe o pedido de deploy | docker, lxd, segredos de serviço, credenciais de escrita |
| deploy | constrói releases e é dona delas | credencial de **escrita** em qualquer repositório |
| serviços | correm a aplicação | capacidade de escrever nas releases |
| backup | dump, restauro, cópias fora | acesso aos repositórios de código |
| humano/agentes | desenvolvimento | (decisão explícita; é aqui que mora o risco) |

Este modelo é ilustrativo; adapta identidades, credenciais e fronteiras às
capacidades do host, plataforma de deploy, fornecedor Git e política local.

Princípios a validar no cenário concreto:

1. Se o processo de build executar dependências ou código não confiável, separa
  a publicação de credenciais de escrita desse processo. Concede escrita só a
  uma etapa autorizada que não execute código arbitrário.
2. Um serviço não deve poder alterar código executável que consome, salvo se
  isso fizer parte explicitamente do modelo. Usa a propriedade e os modos
  exigidos pela política do host; `root:<grupo>` e um motor root são opções
  específicas, não soluções padrão.

## O canal de deploy sem sudo

Se o host Linux usar systemd e polkit, e a configuração instalada confirmar
que o runner não pode executar a operação privilegiada diretamente, um canal
de pedidos pode ser uma opção. `NoNewPrivileges` e `ProtectSystem` têm efeitos
dependentes da unit; não os infiras sem inspecionar a versão e configuração
efetivas. O exemplo seguinte não é universal:

1. O runner envia um pedido autenticado e limitado ao componente e SHA
  permitidos, usando a interface disponível no host.
2. A política identifica o principal exato do runner e restringe a ação a
  unidades/componentes de uma allowlist, sem seleção de unidade, argumentos
  ou instâncias arbitrárias de um template.
3. O pedido tem expiração e consumo único, com prevenção de replay. O validador
  confirma a proveniência do CI e a política de SHA apropriada.
4. A validação e execução ficam ligadas ao mesmo objeto imutável; impede que o
  SHA ou o conteúdo mude entre validação e execução (TOCTOU).
5. Um executor privilegiado realiza apenas a etapa necessária após preflight e
  autorização. Não executa builds ou dependências não confiáveis como root.

Polkit, systemd, D-Bus, ficheiros de pedido e sandbox são exemplos. Valida as
regras instaladas e testa permissões positivas e negativas, seleções arbitrárias,
replay, SHA alterado após validação e proveniência do resultado CI antes de usar
qualquer canal em produção.

## Credenciais

- Usa credenciais de menor privilégio por identidade quando o provider e a
  plataforma o suportarem; uma chave por repositório é uma opção, não uma regra.
- Verifica permissões efetivas nas definições, API ou auditoria do provider para
  o principal e repositório exatos. `git push --dry-run` é apenas consultivo:
  hooks, branches protegidos e políticas do provider tornam o resultado
  inconclusivo. Só faz uma escrita de teste numa ref descartável se for
  explicitamente autorizada e houver limpeza validada.
- Tokens de longa duração fora de homes acessíveis a runners e agentes. Se
  existir um temporário, tem data para morrer e alguém que a cumpra.
- Mantém credenciais fora de locais acessíveis a automação não autorizada, de
  acordo com o secret manager e a política do host. Ficheiros root-owned `0600`
  carregados por systemd são uma opção condicionada, não um requisito geral.

## Topologia de chaves: a mesma chave em quatro sítios

Antes de mexer numa credencial, mapeia onde está configurada e quais identidades
a podem usar. A lista abaixo é um exemplo de uma topologia possível, não uma
enumeração exaustiva nem uma afirmação sobre todos os hosts:

- `~/.ssh/` da conta humana (onde tu e os agentes empurram);
- `/var/lib/<serviço>/.ssh/` da identidade de serviço (o motor de deploys);
- `/etc/<projeto>/<orquestrador>-pull-ssh/` (os *pull steps* clonam com esta,
  em cada execução de flow);
- `/etc/<projeto>/<monitor>-ssh/` (um verificador de saúde).

Descobre as fontes a partir da configuração efetiva, identidade do processo,
secret manager e provider. Usa comandos de inventário apenas quando a plataforma
e a autorização o permitirem; não assumes `/var/lib`, `/etc`, `sudo`, globs ou
um filesystem específico. Enumera caminhos sem perder espaços e compara chaves
públicas por fingerprint; nunca imprimas material privado.

Nomes diferentes podem ser a mesma chave; nomes iguais podem ser chaves
diferentes. O fingerprint identifica a chave pública, mas não prova quem pode
ler a privada nem quais permissões o provider concedeu.

## Escrita concedida a ti é escrita concedida ao runtime

A consequência depende de acesso efetivo: se a identidade de serviço consegue
ler e usar uma chave **partilhada** e alcançar o provider, conceder escrita a
essa chave pode dar escrita **também** ao serviço. Se essa identidade corre
workers, então
código de um trabalho agendado pode empurrar para o ramo principal — o mesmo
ramo que o validador de deploys aceita como verdade para ativar releases. Toda a
revisão que construíste passa a ter uma porta ao lado.

Um padrão possível, quando o provider e a política local o suportarem:

| Identidade | Chave | Permissão |
| --- | --- | --- |
| serviço que só clona em runtime | credencial limitada ao clone | leitura, se suficiente |
| etapa de publicação autorizada | identidade/credencial aprovada pelo provider | apenas as permissões necessárias |
| humanos e agentes | mecanismo definido pela política de acesso | sem separação por chave obrigatória; limitar por função e capacidade efetiva |

O objetivo é reduzir o acesso efetivo de cada identidade, não exigir chaves
SSH distintas quando a plataforma oferece outro controlo equivalente.

Antes de alterar permissões, confirma no provider a sequência suportada, os
consumidores e o impacto durante a transição. Não assumes que uma chave pode ser
convertida nem que um dry-run prova o estado final. Verifica leitura e escrita
pela interface de permissões do provider ou, se autorizado, por uma escrita
real numa ref descartável; `ls-remote` prova apenas leitura.

## Chaves duplicadas podem interromper um runtime

Duas chaves de leitura no mesmo repositório podem parecer desarrumação e uma
delas pode pertencer a um serviço. Removê-las sem inventário pode interromper
um clone ou restart futuro; confirma consumidores e cronologia de uso antes de
agir.

Antes de apagar qualquer credencial, confirma consumidores, política do provider
e recuperação. Só derives a chave pública a partir de uma privada com
autorização para aceder ao segredo; não imprimas nem copies o material privado.

## Sequência segura para apertar isto

1. Inventariar identidades, grupos, credenciais e efeitos no host segundo a
  plataforma real.
2. Propor identidades separadas e migração de segredos conforme a política de
  acesso aplicável.
3. Para mudanças autorizadas, definir rollback ou recuperação antes de alterar
  serviços, credenciais ou canais de deploy.
4. Validar o novo canal com um teste seguro e autorizado, se existir.
5. Remover acessos anteriores só depois de confirmar consumidores, recuperação
  e o resultado esperado.

## Exemplo de implementação

Para avaliar um canal Linux/systemd/polkit, consulta
[references/release-request-contract.md](references/release-request-contract.md).
É orientação ilustrativa, não um template instalável. As units, a regra polkit,
o cliente e o validador têm de ser adaptados, implementados e testados no
repositório que governa o host; este catálogo não os instala.

## Quando não aplicar

Esta orientação não se aplica a runners isolados sem credenciais nem acesso ao
host de produção. Usa-a quando CI, agentes ou automação influenciável partilham
um host de produção ou credenciais de produção com serviços/deploys; confirma
essa fronteira antes de recomendar mudanças.
