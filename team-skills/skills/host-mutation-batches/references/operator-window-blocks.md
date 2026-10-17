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

## Coordenação

- Durante a janela não entram merges em repositórios com deploy automático
  para esse host. Além do risco, um deploy a meio faz falhar as comparações de
  PID sem razão.
- O operador mostra o output de cada bloco antes de passar ao seguinte.
