---
name: diagnose-host-failures
description: Catálogo de padrões de falha operacional em hosts Linux de produção, com foco em ciclo de vida de serviços, identidade, permissões e execução de workers. Usa quando um incidente concreto nesses componentes corresponde a um exemplo; não para falhas genéricas de CI, alertas, agendamentos ou scanners.
---

# Diagnosticar falhas de host

Usa os exemplos como hipóteses para confirmar, não como diagnóstico automático.
Confirma primeiro que o sistema, a identidade e o sintoma correspondem à
entrada. As sondas e correções dependem do ambiente e não concedem autorização
para aceder ao host, contactar serviços remotos ou alterar estado.

O catálogo completo está em `references/catalog.md` e contém 17 entradas.

## Índice por sintoma

**Privilégios**
- `sudo: The "no new privileges" flag is set` → `NoNewPrivileges` na unit mata o setuid.
- Root recebe `Read-only file system` → uma proteção da unit ou do namespace é hipótese; confirma configuração e mount namespace ativos antes de determinar a causa.

**systemd**
- Serviços pararam sozinhos depois de reiniciar outro → `Requires=` propaga o stop, o start não os repõe.
- Um PR endurece uma unit e na verdade remove hardening → o ficheiro do repo estava desatualizado.

**Git usado por serviços no host**
- `fatal: detected dubious ownership` → dono do repositório diferente de quem executa.

**Python e empacotamento**
- `bad interpreter: No such file or directory` num CLI da release → shebang do diretório de staging.
- Script root a correr de um diretório do utilizador → `sys.path[0]` permite substituir módulos.

**Workers e orquestração**
- Ativação "verificada" em menos de um segundo → aceitou o heartbeat do processo anterior.
- O symlink aponta para a versão nova e corre código antigo → as definições clonam um SHA antigo.
- Todos os jobs falham no clone depois de mudar a identidade do serviço → faltam aliases SSH.
- Runs presas em RUNNING há meses → o worker morreu sem transição de estado.

**Configuração em camadas**
- Trabalhos falham num caminho que não está na configuração do host → o valor vem das definições do orquestrador.
- Uma password aparece na API do orquestrador → referências a cofre resolvidas na publicação.
- Um symlink correto e acesso negado → falta travessia num diretório acima.

**Aplicações**
- O serviço está vivo, a API responde, e o dashboard dá 404 → quer escrever dentro do pacote instalado.

**Serviços e estado instalado**
- `InvocationID` vazio logo após a unit correr → unit transitória descarregada.
- `baseline drift` num lote cujo alvo já está instalado → dois lotes no mesmo ficheiro.
- Deploy falha com `exit status 128` e o serviço não pode reiniciar → apagaram a deploy key do serviço.

## Como usar

1. Confirma que o sintoma é de operação do host e corresponde ao âmbito desta Skill.
2. Confirma plataforma, serviço, identidade e configuração antes de escolher uma sonda.
3. Identifica se a sonda requer privilégios, altera estado ou contacta um serviço remoto. Executa-a apenas se for aplicável e estiver autorizada; caso contrário, apresenta-a ao operador sem a executar.
4. Trata a correção como hipótese. Explica os pré-requisitos e pede autorização antes de qualquer mudança; não a apliques automaticamente.
5. Se a falha não estiver aqui e for nova, propõe uma entrada após confirmar o diagnóstico. Só edites o catálogo se este workspace for o repositório canónico da Skill e o utilizador tiver autorizado essa alteração.

## Regra geral que resume metade do catálogo

**Nunca aceites como prova um estado que já era verdade antes da mudança.**
Um processo vivo, um `is-active`, um registo `ONLINE`, um `/health` genérico:
nada disto distingue a versão nova da antiga.
