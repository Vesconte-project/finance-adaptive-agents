# Contrato para um script de lote

Se um workflow de host coordenado usar um script de lote, o script é específico
do host e fica no repositório que o governa. Antes de o criar, identificar a
fonte versionada, unidades afetadas, caminhos de estado, permissões, janela e
aprovação aplicáveis. Não pressuponhas systemd, root, Git remoto ou um
determinado layout.

| Ação | Contrato mínimo |
| --- | --- |
| `stage` | Prepara uma fonte imutável identificada (commit, digest de artefacto, versão assinada ou equivalente) num local controlado; verifica origem, integridade, permissões e delta autorizado. Propriedade root e `git archive` são opções quando aplicáveis. |
| `plan` | Só lê o instalado. Mostra identificador da fonte, âmbito autorizado, baseline, mudanças, reinícios, indisponibilidade e recuperação. Recusa alterações extra ou drift antes de qualquer escrita. |
| `apply` | Exige confirmação explícita, revalida a mesma fonte imutável e âmbito aprovado, repete o preflight, guarda backup validado antes de cada alteração e verifica o comportamento real depois. Regista estado ligado à fonte e à tentativa. |
| `rollback` | Confirma a origem dos backups e restaura apenas alterações reversíveis cobertas pelo lote. Para operações externas ou não reversíveis, exige recuperação/forward-fix verificado ou exclui-as explicitamente do rollback automático. |

Inclui um teste em que dois lotes são aprovados antes da aplicação: ao aplicar
o primeiro com uma fonte que também contém alterações do segundo, o lote deve
recusar ou usar uma fonte separadamente aprovada, e nunca instalar alterações
do segundo em silêncio.

Não copiar um esqueleto genérico para root sem revisão. Os detalhes mais
propensos a erro são: decodificar um `git archive` binário como texto, seguir
symlinks durante extração ou cópia, aceitar receipt manipulável por uma conta
de serviço, tratar `FAILED_ROLLED_BACK` como bloqueio permanente, e confundir
um alvo já instalado com drift. Cobrir estes casos nos testes do lote.
