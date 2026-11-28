# Contornos de ferramentas verificados

Exemplos observados numa estação concreta (orquestrador local, MCP do GitHub, uma CLI de
estação). Não são universais: confirma no teu ambiente e usa só os que correspondem.

- **Respostas grandes de MCP** (por exemplo a lista de ficheiros de um PR) são gravadas num
  ficheiro JSON de uma só linha. Lê-o com um script (`python3 -I`), não com leitura por linhas.
  Extrai só nomes, contagens e os patches que vais rever.
- **`jq` ou `gh` ausentes.** Usa `python3 -I` para JSON e as ferramentas MCP do GitHub para PRs.
- **check-runs com 403** usando o token do agente não prova falta de permissão de escrita.
  Usa o comando de espera de CI da estação, que lê o estado agregado.
- **Atualizar uma página por substituição de texto** falha com diferenças de maiúsculas ou
  espaços. Volta a ler a página e copia o texto exato.
- **Instalar a ferramenta da estação a partir da cópia instalada** pode ser recusado; corre-a
  a partir do checkout com commit.
- **Fechar uma unidade sem PR** exige registar um resultado; uma unidade com PR exige handoff
  com repositório, ramo, commit, PR e estado da CI.
- **Ferramenta de estado de tarefas delegadas** pode exigir o identificador completo do nó
  (`node:delegated-task:…`), não só o UUID final.
