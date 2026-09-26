# Contrato de componente e caminhos

Se o host usar um manifesto por componente, guarda-o com os controlos de acesso
exigidos pela plataforma e política local (root-owned quando aplicável). Deve
identificar, conforme o workflow: origem e política de branch/SHA, runtime e
lock, entradas de build, serviços, identidade, estado externo, dependências,
readiness e recuperação. Um repositório pode gerar vários componentes; um
componente composto pode fixar SHAs de vários repositórios.

Quando se usar systemd, a unit pode apontar para `current/<componente>` e
carregar ficheiros de ambiente fora do checkout. Confirma as regras de merge e
a ordem efetiva dos `EnvironmentFile` na versão instalada, sem assumir uma
precedência genérica. Separa caminhos de credenciais quando isso corresponder
ao modelo de segurança. O serviço precisa apenas das permissões necessárias no
estado e artefactos, não de escrita na release.

Num `plan` autorizado, compara o contrato com os serviços, destinos, permissões,
receipts e caminhos realmente usados no host. No `apply`, verifica o processo ou
flow que usa a release e grava `verified` só depois de obter evidência adequada.
Um exemplo de unit ou JSON de outra máquina não serve como contrato instalável.
