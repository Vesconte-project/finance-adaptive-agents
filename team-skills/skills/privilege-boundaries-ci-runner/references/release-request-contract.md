# Exemplo: pedido de release sem sudo em Linux/systemd

Este é um exemplo para hosts que usam Linux, systemd, D-Bus e polkit. Só se
aplica depois de confirmar versões, permissões e política instaladas. Adapta os
controlos equivalentes na plataforma real; este documento não define um
contrato universal nem autoriza operações.

Quando a política de release exigir CI aprovado, o workflow valida a proveniência
do resultado e o SHA autorizado. Se houver vários componentes, só regista vários
pedidos antecipadamente quando isso for seguro, idempotente e não iniciar
deploys antes do gate; caso contrário, usa uma transação ou mecanismo atómico.

Neste exemplo, o cliente aceita apenas componentes conhecidos e SHAs completos
segundo a política de promoção; pedidos e armazenamento são adaptados ao host.
Se houver polkit, autoriza apenas a ação e instâncias permitidas para a
identidade exata do runner, sem seleção arbitrária de template/unit. O executor
privilegiado, se existir, valida o pedido e impede replay e TOCTOU entre SHA
validado e conteúdo executado. `O_NOFOLLOW`, validação por descritor, ownership,
modo e sandbox são opções dependentes do sistema; implementa controlos
equivalentes adequados na plataforma alvo. Não executes build ou dependências
não confiáveis como root.

O estado do pedido deve distinguir aceitação, adiamento, conclusão verificada,
falha e expiração segundo o workflow. Um pedido adiado conserva estado e retry
se a plataforma suportar essa semântica; uma consulta ao orquestrador que falha
não autoriza reiniciar serviços. O workflow pode aceitar um pedido ainda
adiado, mas deve dizer explicitamente que não está em produção. Se o reporte
posterior falhar, não confundas essa falha com o resultado da ativação.

Antes de usar, testa autorização positiva e negativa, replay, pedido inválido,
SHA/conteúdo alterado após validação, adiamento e falha do reporte conforme os
mecanismos existentes. Só testes polkit e diretivas `NoNewPrivileges`,
`ProtectSystem` e `ReadWritePaths` quando o host usar systemd/polkit; confere a
configuração efetivamente instalada. O código concreto e os controlos
equivalentes pertencem ao repositório que governa a plataforma.
