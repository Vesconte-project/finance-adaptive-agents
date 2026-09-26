---
name: greenfield-host-setup
description: Planear a primeira instalação de um host de produção apenas quando dados persistentes estão num checkout/volume que o deploy ou rebuild pode substituir, e o workflow de deploy executa código/entradas controláveis por contribuidores menos confiáveis com acesso a recursos de produção. Sem ambas as condições, não se aplica.
---

# Dia 1 de um servidor que vai importar

Esta é uma lista de decisões a avaliar antes da primeira instalação, não uma
receita de plataforma. Confirma sistema operativo, runtime, dados, disponibilidade,
modelo de ameaça e workflow de deploy antes de escolher controlos. Os exemplos
Linux, systemd, Docker/LXD e GitHub Actions são condicionais; os custos e riscos
dependem do ambiente.

## 0. Decide o que esta máquina é

Confirma ambas as condições antes de usar esta skill:

1. Dados persistentes estão dentro de um checkout, volume implícito ou outro
  caminho que o deploy/rebuild realmente substitui, limpa ou recria.
2. O workflow executa código ou entradas (por exemplo, pull requests ou
  artefactos) que contribuidores menos confiáveis podem controlar, e esse
  workflow consegue alcançar credenciais ou recursos de produção.

Se qualquer condição faltar, esta skill não se aplica; escolhe orientação
específica ao problema real.

## 1. Identidades antes de serviços

Decide, antes de instalar serviços, se o sistema operativo e o modelo de
execução suportam identidades separadas e quais fronteiras de privilégio são
necessárias. Contas dedicadas são uma opção quando aplicável, não um requisito
universal. Por exemplo, um host Unix pode separar:

- `<proj>-deploy`: constrói e é dona das releases. Shell `nologin`.
- `<proj>-svc`: corre os serviços (ou uma por domínio, se quiseres isolar).
- `<proj>-runner`: o runner de CI, sem grupos suplementares.
- `<proj>-backup`: backups e restauro.

Se existirem grupos como `docker` ou `lxd`, confirma as capacidades reais do
daemon e dos membros antes de decidir a associação; membership não prova por si
só controlo root. Aplica exceções apenas com necessidade e aprovação explícitas.

Define como o operador humano e os agentes são autenticados e autorizados,
segundo as capacidades disponíveis. Não assumes `sudo`, acesso root, uma
identidade dedicada para agentes ou acesso a todos os segredos; verifica as
permissões efetivas e o modelo de isolamento.

> **Risco a avaliar:** mudar identidades depois do deploy pode exigir rever
> credenciais, ownership, permissões e dependências; o impacto depende dos
> serviços e do runtime.

## 2. Declara os caminhos antes de existir estado

O exemplo seguinte assume um host Linux com filesystem POSIX; confirma que os
caminhos e controlos são adequados antes de os adotar:

```text
/srv/<proj>/releases/   código imutável
/srv/<proj>/current/    symlinks
/srv/<proj>/state/      tudo o que muda e importa
/srv/<proj>/artifacts/  resultados grandes
<config-path>           paths, com permissões conforme política
<secret-store>          credenciais via mecanismo aprovado
```

Se o runtime suportar configuração por variáveis, a aplicação pode receber
nomes de configuração em vez de caminhos hardcoded. Mantém segredos fora de
ficheiros legíveis pelo código de deploy não confiável; um `EnvironmentFile`
root-owned é apenas uma opção systemd, com permissões e exposição avaliadas.
Define separadamente quais diretórios podem ser escritos por cada serviço.

> **Risco a avaliar:** estado armazenado num caminho que o deploy substitui pode
> ser perdido ou ficar inconsistente; verifica a política de limpeza e
> persistência do workflow real.

## 3. O primeiro serviço já corre de uma release

Se o serviço for executado a partir de um checkout mutável que o deploy possa
substituir, avalia releases identificadas por commit, artefactos reproduzíveis e
separação entre código e estado. Systemd, symlinks, lockfiles e propriedade
root são exemplos condicionais. Confirma o rollback disponível; um checkout
mutável não implica por si só que não exista rollback.

## 4. O canal de deploy antes do primeiro deploy automático

Se o deploy vier de automação influenciável, define como a identidade é
autenticada, quais componentes pode solicitar e como se prova a origem do
commit. Um runner isolado, D-Bus, systemd, polkit e uma unit privilegiada são
opções para hosts que suportem esse modelo; usa controlos equivalentes noutros
ambientes e exige autorização para a operação.

Se usares GitHub Actions, `workflow_run` é apenas um exemplo: valida workflow,
evento, repositório, ref, SHA e proveniência antes de disponibilizar segredos.
Não assumes que `conclusion == 'success'` sozinho prova que o commit autorizado
foi verificado. `NoNewPrivileges` e `ProtectSystem` dependem da unit e versão.

## 5. Backups e restauro no mesmo dia dos dados

- Escolhe backup consistente com o motor de dados e a política de retenção;
  testa o restore num destino isolado quando permitido.
- Inclui estado, artefactos e configuração necessários para recuperação, mas
  trata segredos segundo uma política de cifragem, acesso e recuperação de
  chaves que não dependa de uma única pessoa.
- Executa ferramentas de backup a partir de uma origem controlada e verificada;
  root-owned é uma opção quando a plataforma e o modelo de privilégio o
  exigirem.

> **Risco a avaliar:** sem cópias consistentes e restore testado, dados ou
> credenciais podem não ser recuperáveis após falha.

## 6. Um caminho de reconstrução, desde o início

Se a plataforma e o risco justificarem reconstrução automatizada, prepara um
procedimento idempotente que configure apenas os recursos suportados e restaure
estado a partir de cópias verificadas. Não automatizes permissões privilegiadas
nem ações destrutivas sem revisão e autorização.

Testa-o num ambiente isolado equivalente, quando disponível, e regista os
limites de fidelidade desse ensaio.

> **Risco a avaliar:** sem passos de recuperação documentados, a reconstrução
> pode demorar ou depender de conhecimento não registado.

## 7. Schema separado do código, desde a primeira migração

Se a aplicação tiver schema versionado e suportar migrações explícitas, define
compatibilidade entre versões e separa operações de dados do deploy de código
quando necessário. Os comandos `plan`/`apply`/`verify` e a política de backup
dependem da ferramenta e da aplicação; confirma o que o rollback realmente
consegue reverter.

> **Risco a avaliar:** rollback de código pode não reverter alterações de schema
> ou dados; documenta a recuperação específica da aplicação.

## 8. Só depois, conveniências

Adiciona ferramentas apenas após definir necessidade, permissões, estado e
fronteiras de rede segundo as capacidades reais da plataforma.

## Verificação do dia 1

Antes de dizeres que está pronto, prova cada uma destas:

- [ ] Foram identificados os serviços, estado persistente e políticas de deploy
  que se aplicam a este host.
- [ ] Permissões e identidades efetivas foram verificadas pelas interfaces
  suportadas; não se inferiu acesso apenas por grupos ou nomes.
- [ ] O deploy e o rollback foram testados num ambiente/fluxo seguro, se
  disponíveis e autorizados; limitações estão documentadas.
- [ ] Backups e restore foram verificados segundo a aplicação e a política de
  acesso/recuperação.
- [ ] Segredos e dados pessoais não foram expostos nos resultados de validação.
- [ ] Existe um procedimento de reconstrução apenas se esse requisito fizer
  parte do modelo operacional.

Marca apenas verificações efetivamente realizadas. Se uma não se aplicar ou não
puder ser autorizada, regista a limitação em vez de a presumir concluída.
