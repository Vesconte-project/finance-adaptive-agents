# Contrato para um script de lote

O script é específico do host e fica no repositório de infraestrutura. Antes
de o criar, identificar fonte versionada, unidades afetadas, caminhos de
estado, dono de cada diretório, janela de trabalho e confirmação humana.

| Ação | Contrato mínimo |
| --- | --- |
| `stage` | Exporta o commit exato para uma árvore root-owned após verificar integridade, origem e permissões. Recusa arquivo com symlink ou caminho que escape do destino. |
| `plan` | Só lê o instalado. Mostra fonte, baseline, mudanças, reinícios, indisponibilidade e comando de rollback. Recusa drift antes de qualquer escrita. |
| `apply` | Exige confirmação explícita, repete o preflight, guarda backup validado antes de cada alteração e verifica o comportamento real depois. Regista receipt atómico ligado ao commit e à tentativa. |
| `rollback` | Confirma a origem dos backups e restaura apenas o que o lote alterou. Verifica o estado reposto e regista separadamente restauração e verificação. |

Não copiar um esqueleto genérico para root sem revisão. Os detalhes mais
propensos a erro são: decodificar um `git archive` binário como texto, seguir
symlinks durante extração ou cópia, aceitar receipt manipulável por uma conta
de serviço, tratar `FAILED_ROLLED_BACK` como bloqueio permanente, e confundir
um alvo já instalado com drift. Cobrir estes casos nos testes do lote.
