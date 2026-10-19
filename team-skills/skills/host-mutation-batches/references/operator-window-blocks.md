# Blocos de janela executados por um operador

Quando o lote não é um script com `stage`/`plan`/`apply`, mas uma sequência de
blocos que um operador humano cola numa janela aprovada, as mesmas
propriedades têm de viver dentro de cada bloco. Aprendido em janelas de
backups e de migrações de schema num host único com deploys automáticos.

## Preparar separado de instalar

- A preparação é um passo próprio, antes da janela, que **não instala nada**:
  cria uma release root-owned e só de leitura a partir do merge commit (não do
  commit do PR), compara byte a byte os ficheiros com o commit revisto, valida
  o manifesto sem ligar à base, e sela. Recusa se o destino já existir.
- Um helper que corre como root é copiado para um diretório root `0700`, e o
  checksum é validado antes de o executar. Nunca executes como root a partir
  de um checkout de outro utilizador.
- Se a preparação falhar, não a repitas às cegas: guarda o output, vê o que
  ficou para trás e só depois decide.

## Cada bloco protege-se a si próprio

- **Janela no próprio bloco:** recusa fora do horário aprovado e quando o
  tempo que falta é menor do que o bloco precisa (por exemplo, 150 minutos
  para backup, reposição de teste e manutenção). O operador pode atrasar-se;
  o bloco não pode confiar nisso.
- **Janelas recorrentes proibidas** (backups diários, manutenção semanal,
  outras janelas) verificadas para todos os minutos que o bloco vai ocupar,
  não só para o início.
- **Alvo fixado:** o bloco confirma que a configuração aponta para a release
  e o commit esperados antes de agir.

## Estado anterior e retorno

- Guarda o estado de partida antes de mexer: units, estado dos timers, e
  `MainPID`/`NRestarts` dos serviços que não deviam mudar.
- Para timers durante o bloco e repõe-nos ao estado anterior num `trap` de
  saída, também em caso de falha.
- Rollback por `trap`: repõe a unit anterior, fecha o login novo, repõe o
  timer, e termina com uma linha que diz o que foi reposto.
- No fim, compara os serviços com o estado de partida. Um PID diferente num
  serviço que não devia ser tocado é falha.

## Recibos como prova

- Cada ação tem de produzir **exatamente um recibo novo** com o estado `_ok`
  esperado, e nenhum ficheiro temporário (`.pending`) pode ficar. Não basta o
  código de saída.
- Valida dono, modo e tipo do recibo, não só o conteúdo.

## Helpers escritos para a janela

Quando o bloco chama um helper preparado para essa janela (um script Python ou
shell revisto), os erros repetem-se de helper para helper. Observado em
18–19/10/2026:

- **Sem datas fixas.** Um guard `date == <dia aprovado>` bloqueia o corte se a
  janela passar da meia-noite, e pior, bloqueia os rollbacks. O guard verifica
  as janelas proibidas e o tempo que o passo precisa, não o calendário.
- **Os rollbacks não passam pelos guards de avanço.** Um rollback exige root e
  respeita as janelas proibidas, mais nada: não depende da data, do estado das
  flags, nem de o estado instalado ser o esperado. Senão, o caminho de recuperação
  falha precisamente quando é preciso.
- **SHAs e versões são parâmetros verificados contra o instalado**, não
  constantes. Um merge com deploy automático entre a preparação e a janela muda
  o componente instalado; o helper deve recusar com uma mensagem clara, e o
  preparador volta a fixar. Não escondas o SHA dentro do código.
- **O snapshot lista tudo o que o helper vai tocar**, incluindo dependências
  acrescentadas por PRs recentes (um script novo de que a rotação passou a
  depender, uma política que vai mudar). Compara a lista com o diff da release.
- **Identidades novas sem LOGIN até haver password**, verificado no catálogo
  antes de abrir o login. Se o servidor tiver regras `trust` locais, um login sem
  password aberto entra sem nada.
- **Comparações exatas com linha de base**, não "zero avisos": regista os avisos
  conhecidos antes e exige igualdade exata depois.
- **Margens de tempo a partir de durações medidas** (journal das execuções
  anteriores), declaradas por bloco.

Se o mesmo tipo de operação se repete, transforma o helper num procedimento
versionado e testado no repositório de infraestrutura, invocado com parâmetros,
em vez de escrever outro na próxima janela.

## Coordenação

- Durante a janela não entram merges em repositórios com deploy automático
  para esse host. Além do risco, um deploy a meio faz falhar as comparações de
  PID sem razão.
- O operador mostra o output de cada bloco antes de passar ao seguinte.
