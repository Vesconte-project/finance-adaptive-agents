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

## Instaladores que geram inputs e se verificam a si próprios

Lições de uma instalação de um motor de releases num host de produção (2026-10), em que a
primeira tentativa foi revertida sozinha e a segunda passou:

- **Corre a verificação do código novo contra o host no `plan`, antes de instalar.** Carrega
  o helper novo a partir da fonte preparada, com inputs temporários root-only, e executa as
  mesmas funções de admissão que vão correr depois do apply (inventário, capacidade). Dois
  defeitos que só existiam naquele host (`/tmp` em tmpfs e templates `@` do systemd) foram
  encontrados assim, sem tocar em nada.
- **Imprime o código da recusa.** Exceções com códigos fixos (`STORAGE_*`, `STAGING_*`) podem
  sair tal como estão. Imprimir só o nome da classe obrigou a uma volta extra para descobrir
  a causa. Mensagens livres continuam proibidas.
- **Gera inputs a partir do estado observado e rotula a origem.** Quando o contrato exige
  inputs que o host ainda não tem (orçamentos, registos de referências, ledgers, baselines),
  deriva-os de observações no momento (tamanhos medidos, recibos atuais, ausência verificada
  de intenções na API) e escreve no próprio ficheiro como foram derivados. Recusa se a
  observação contradisser a suposição (por exemplo, se já existirem intenções a adotar). Nunca
  escrevas valores plausíveis inventados.
- **Rollback automático verificado.** Se a verificação depois do apply falhar, repõe os bytes,
  os modos e os donos do snapshot e confirma os hashes. Depois, verifica fora do bloco que os
  ficheiros instalados voltaram a coincidir com a revisão anterior.
- **Um diretório de estado novo por tentativa.** Um diretório de estado fixo que recusa
  "já existe" bloqueia a segunda tentativa depois de um rollback. Versiona-o (`-v2`, `-v3`) ou
  inclui o identificador da tentativa.
- **Para remoções em massa, volta a verificar no momento de apagar.** Um plano congelado é só
  a lista de candidatas. No momento de apagar, recalcula as proteções (atual, predecessores
  verificados, processos, units, pedidos pendentes, documentos de recuperação), move primeiro
  as candidatas para uma quarentena no mesmo filesystem, verifica a saúde e só então apaga.
  Se a saúde falhar, repõe a partir da quarentena.
