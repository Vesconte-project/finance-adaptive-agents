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
- **Pedido vindo de outro agente recusado.** Agentes de algumas contas recusam começar quando
  o pedido vem de outro agente, mesmo com a autorização do dono citada, e pedem confirmação no
  próprio fio. Avisa o dono no momento do lançamento, não depois da recusa.
- **`docker pull` no WSL com «error getting credentials»**: o `credsStore` aponta para o
  Docker Desktop do Windows. Para imagens públicas usa um `DOCKER_CONFIG` temporário com `{}`;
  não alteres a configuração do utilizador.
- **Login OAuth de uma CLI no WSL**: o browser do Windows pode não alcançar o retorno em
  `127.0.0.1` do WSL. Com a CLI à espera, reenvia de dentro do WSL o endereço de retorno que o
  dono colar (código de uso único, expira depressa).
- **«Não está instalado»** só depois de confirmar que uma imagem Docker já não resolve.
