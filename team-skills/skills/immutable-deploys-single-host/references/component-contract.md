# Contrato de componente e caminhos

O manifesto root-owned de cada componente deve identificar: repositório e
branch, SHA requerido, runtime e lock, entradas de build, units, identidade,
estado externo, dependências, verificação de prontidão e rollback. Um
repositório pode gerar vários componentes; um componente composto pode fixar
SHAs de vários repositórios.

A unit aponta para `current/<componente>` e carrega ficheiros de ambiente
instalados fora do checkout. Se houver mais de um `EnvironmentFile`, confirmar
a ordem efetiva: a última atribuição prevalece. Separar um ficheiro de
caminhos sem segredos do ficheiro de credenciais root-owned. O serviço deve
poder escrever no estado e nos artefactos, mas não na release.

No `plan`, comparar contrato, unit instalada, destinos de symlink, modos,
receipts e paths de estado com a máquina. No `apply`, verificar o processo ou
flow que usa a release e gravar `verified` só depois dessa prova. Um exemplo
de unit ou JSON de outra máquina não serve como contrato instalável.
