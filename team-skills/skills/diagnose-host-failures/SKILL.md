---
name: diagnose-host-failures
description: Catálogo de padrões de falha operacional em hosts Linux de produção, com foco em ciclo de vida de serviços, identidade, permissões e execução de workers. Usa quando um incidente concreto nesses componentes corresponde a um exemplo ou exige recolha privilegiada de metadados; não para falhas genéricas de CI, alertas, agendamentos ou scanners.
---

# Diagnosticar falhas de host

Usa os exemplos como hipóteses para confirmar, não como diagnóstico automático.
Confirma primeiro que o sistema, a identidade e o sintoma correspondem à
entrada. As sondas e correções dependem do ambiente e não concedem autorização
para aceder ao host, contactar serviços remotos ou alterar estado.

O catálogo completo está em `references/catalog.md` e contém 20 entradas.

## Índice por sintoma

Cada seta aponta para uma hipótese a confirmar com a entrada detalhada; não
atribui a causa só pelo sintoma.

**Privilégios**
- `sudo: The "no new privileges" flag is set` → possível `NoNewPrivileges` a impedir a elevação por setuid.
- Root recebe `Read-only file system` → uma proteção da unit ou do namespace é hipótese; confirma configuração e mount namespace ativos antes de determinar a causa.

**systemd**
- Serviços ficaram parados após `stop` e depois `start` de outro → possível propagação de stop por dependência; distinguir de `restart` explícito.
- Um PR endurece uma unit e na verdade remove hardening → possível divergência entre ficheiro revisto e configuração instalada.

**Git usado por serviços no host**
- `fatal: detected dubious ownership` → possível divergência de proprietário e identidade executora.

**Python e empacotamento**
- `bad interpreter: No such file or directory` num CLI da release → possível shebang ainda ligado ao staging.
- Script root a correr de um diretório do utilizador → possível substituição de módulos via diretório do script.

**Workers e orquestração**
- Ativação "verificada" em menos de um segundo → possível heartbeat da instância anterior.
- O symlink aponta para a versão nova e corre código antigo → possível SHA antigo nos pull steps, se o backend os usar.
- Todos os jobs falham no clone depois de mudar a identidade do serviço → possível falta de configuração/acesso SSH da identidade nova.
- Runs presas em RUNNING há meses → possível perda do worker sem transição de estado.

**Configuração em camadas**
- Trabalhos falham num caminho que não está na configuração do host → possível override nas definições do backend.
- Uma password aparece na API do orquestrador → possível referência a cofre resolvida para plaintext na publicação.
- Um symlink correto e acesso negado → possível falta de travessia num ancestral.

**Aplicações**
- O serviço está vivo, a API responde, e o dashboard dá 404 → possível tentativa de escrita no pacote instalado; confirmar logs.

**Base de dados e workers sob limites**
- `SQLSTATE 53100` (`could not resize shared memory segment … No space left on device`) numa query grande → possível `/dev/shm` pequeno no contentor PostgreSQL com paralelismo.
- Um worker de Python preso no limite de memória e a crescer em swap → possível carregamento de um conjunto inteiro em objetos Python; confirmar o pico e o limite de swap da unit.

**Serviços e estado instalado**
- `InvocationID` vazio logo após a unit correr → possível descarga do estado; confirmar lifecycle e referências.
- `baseline drift` num lote cujo alvo já está instalado → possível sobreposição de instalações com baseline no mesmo ficheiro.
- Deploy falha com `exit status 128` e o serviço não pode reiniciar → possível remoção de uma chave necessária ao clone de arranque.

## Leitura privilegiada de metadados

Quando o diagnóstico precisa de um leitor privilegiado autorizado, lê
[references/sealed-read-only-readers.md](references/sealed-read-only-readers.md):
selagem, admissão atual, identidade efetiva, transação só de leitura e saída por
allowlist. Leitura da base não autoriza alterações nem contacto a fornecedores.

## Como usar

1. Confirma que o sintoma é de operação do host e corresponde ao âmbito desta Skill.
2. Confirma plataforma, serviço, identidade e configuração antes de escolher uma sonda.
3. Identifica se a sonda requer privilégios, altera estado ou contacta um serviço remoto. Executa-a apenas se for aplicável e estiver autorizada; caso contrário, apresenta-a ao operador sem a executar.
4. Trata a correção como hipótese. Explica os pré-requisitos e confirma que a autorização existente cobre a mudança e o alvo; se não cobrir, pede-a antes de agir.
5. Se a falha não estiver aqui e for nova, propõe uma entrada após confirmar o diagnóstico. Só edites o catálogo se este workspace for o repositório canónico da Skill e o utilizador tiver autorizado essa alteração.

## Regra geral que resume metade do catálogo

**Nunca aceites como prova um estado que já era verdade antes da mudança.**
Um processo vivo, um `is-active`, um registo `ONLINE`, um `/health` genérico:
nada disto distingue a versão nova da antiga.
