# Contrato do pedido de release sem sudo

O workflow só pede deploy de um SHA cujo CI passou. Se um repositório gera
vários componentes, escrever todos os pedidos antes de interpretar o estado
agregado, para que um adiamento não elimine os restantes.

O cliente do runner aceita apenas componente conhecido e SHA completo. Escreve
o pedido atomicamente no diretório próprio do runner. A regra polkit autoriza
apenas o `start` das instâncias permitidas, para a identidade exata do runner.
A unit root valida o pedido antes de chamar o motor: diretório e ficheiro por
descritor, `O_NOFOLLOW`, dono, modo, tamanho, formato, SHA no topo do branch e
política de CI. O motor atua fora do sandbox do runner e grava receipt.

O estado do pedido distingue `verified`, `deferred`, `pending`, `failed` e
`expired`. Um pedido adiado conserva estado e retry; a consulta ao
orquestrador que falha não autoriza reiniciar serviços. O workflow pode aceitar
um pedido ainda adiado, mas deve dizer explicitamente que não está em
produção. Uma ativação verificada não pode tornar-se falha só porque o reporte
posterior falhou.

Antes de instalar, testar autorização positiva e negativa do polkit, pedido
com symlink, modo/dono errado, SHA inválido, duplicação, adiamento e falha do
reporte. Conferir `NoNewPrivileges`, `ProtectSystem` e `ReadWritePaths` nas
units instaladas. O código concreto pertence ao repositório da plataforma.
