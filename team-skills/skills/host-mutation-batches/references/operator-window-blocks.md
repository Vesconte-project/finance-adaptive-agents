# Blocos de janela executados por um operador

Quando o workflow aprovado usa blocos que um operador cola numa janela, em vez
de um script com `stage`/`plan`/`apply`, cada bloco conserva o contrato de fonte,
alvo, pré-condições, evidência e recuperação. Descobre primeiro plataforma,
identidades, serviços, scheduler, armazenamento e procedimento de aprovação.

Os exemplos abaixo vêm de janelas de backups e schema num host Linux único,
com deploy automático; não exigem essa infraestrutura noutros ambientes.
Os relatos de helpers de 18–20/10/2026 são aprendizagens locais, não prova
independente de segurança de outro host.

## Preparar separado de instalar

- Prepara antes da janela sem instalar no alvo: identifica a fonte imutável
  aprovada, verifica origem, integridade e âmbito e protege-a contra alteração
  por identidades fora da cadeia de confiança. No workflow observado, era uma
  release root-owned só de leitura do merge commit, comparada byte a byte com
  o conteúdo revisto e selada. Outros workflows podem usar artefactos assinados;
  não se exige merge commit quando Git/merge não faz parte do processo.
- Executáveis privilegiados e seus ancestrais têm de estar protegidos contra
  substituição. No exemplo root, um helper era copiado para um diretório root
  `0700` e o digest validado antes de executar. Escolhe identidade/permissões
  equivalentes no alvo; propriedade root sozinha não prova integridade.
- Valida manifestos sem contactar a base quando a validação é só estrutural;
  sondas de acesso reais são passos separados cobertos pela autorização.
- Recusa colisões com um destino de preparação já existente sem o validar.
  Se falhar, preserva a evidência e reconcilia o estado parcial antes de repetir.

## Cada bloco protege-se a si próprio

- **Intervalo aprovado completo:** guarda início e fim com datas e timezone
  explícitos (ou instantes UTC), incluindo janelas que atravessam meia-noite.
  Revalida o instante atual e exige que execução e verificação caibam antes
  do fim autorizado, segundo uma duração conservadora medida e margem para
  recuperação. Um horário recorrente livre não autoriza outra data. Mudança
  de dia ou DST não cria nem prolonga autorização.
- **Conflitos recorrentes:** verifica sobreposição em todo o intervalo previsto,
  não só no início, usando a configuração efetiva do scheduler e os trabalhos
  já em curso. Mantém esta prova separada da pertença à janela autorizada.
- **Alvo fixado:** confirma identidade do host/serviço, fonte e configuração
  efetiva antes de agir. Se drift mudar o delta ou o risco aprovado, recusa e
  prepara um plano revisto; não atualizes o alvo silenciosamente.

## Estado anterior e retorno

- Regista o estado relevante antes de mexer. Em systemd pode incluir units,
  estado dos timers, invocações e `MainPID`/`NRestarts` dos serviços que não
  deviam mudar; noutros gestores usa evidência equivalente. Um PID sozinho
  pode ser reutilizado e não demonstra identidade.
- Suspende agendamentos apenas quando o plano aprovado o exige. Regista o
  estado anterior e o efeito de reativar: um timer persistente pode disparar
  trabalho em atraso. Só o repões quando os recursos dependentes estiverem
  consistentes e seguros para esse trabalho, segundo a estratégia validada.
- Um `trap` pode iniciar limpeza, mas não prova rollback e pode nem correr
  numa perda de energia ou término forçado. Mantém estado recuperável por um
  operador posterior. O handler não esconde a falha original nem anuncia
  sucesso se alguma restauração ou verificação falhou.
- O rollback confirma autorização de recuperação, alvo exato, identidade de
  execução, backups íntegros e compatíveis e ausência dos conflitos relevantes
  para restaurar. Não exige que o estado parcial satisfaça guards de avanço
  como versão-alvo instalada ou flag de sucesso. Define esses critérios de
  recuperação antes do apply; não os elimina para desbloquear uma emergência.
- O horário de recuperação segue a política aprovada: pode permitir terminar
  recuperação fora da janela de avanço ou exigir intervenção específica. Não
  bloqueies universalmente rollback por data/janelas recorrentes, nem assumes
  permissão ilimitada para restaurar fora delas.
- Restaura o conjunto coerente previsto pelo lote, não uma lista fixa universal
  de unit, login e timer. Valida configuração, dados e disponibilidade após
  cada recuperação. Se incompleta, mantém suspenso o trabalho inseguro e
  reporta recursos pendentes e próximo passo autorizado; não diz “reposto”.

## Recibos como prova

Define o contrato de evidência por ação e tentativa: identidade do alvo, fonte,
resultado, alterações e recuperação. No workflow observado exigia-se um recibo
novo `_ok` por ação e nenhum `.pending` residual; esse nome e cardinalidade são
convenções locais, não universais. Valida autenticidade, tipo e permissões do
artefacto conforme o modelo de ameaça; código de saída sozinho não basta.
Preserva tentativas falhadas e não sobrescreve evidência de execução anterior.

## Helpers escritos para a janela

- **Versões como parâmetros verificados:** confirma os identificadores aprovados
  contra o instalado; um deploy entre preparação e janela pode causar drift.
  Não escondas um SHA fixo no código nem aceites o novo SHA automaticamente.
- **Snapshot completo:** inclui todos os recursos tocados, incluindo dependências
  recentes, e compara com o delta da release. Para ações não reversíveis define
  recuperação/forward-fix antes de começar; backup de ficheiros não reverte
  credenciais ou efeitos externos por si só.
- **Identidades novas:** quando a base suportar `LOGIN`/`NOLOGIN`, pode ser
  adequado criar a identidade sem login até a autenticação estar configurada.
  Confirma o motor, regras efetivas (incluindo `trust` se existir) e teste de
  acesso previsto. Não imponhas semântica PostgreSQL a outro motor.
- **Linha de base contextual:** compara avisos e estados relevantes com o
  baseline aprovado. Não normalizes um aviso novo por já haver avisos antigos.
- **Durações medidas:** deriva margens por bloco de execuções comparáveis;
  inclui verificações e recuperação, não só a mutação.

## Estado de partida da operação, não o alvo da release

Entre janelas, o alvo fica muitas vezes num estado intermédio: a release nova já
está instalada, mas as suas migrações só entram num corte posterior. Código ou
verificadores dessa release assumem o estado final. No caso observado:

- a retoma de uma operação exigia versões iguais ao manifesto completo e teria
  recusado antes de começar, porque o manifesto já incluía as migrações do corte;
- a ativação de um login com a ferramenta da release nova comparou a base com o
  catálogo final e recusou por centenas de diferenças estruturais, antes de
  mexer em qualquer coisa. A prova da CI estava verde porque só cobria o estado
  final.

Cada operação declara explicitamente o estado de que parte (versões por schema,
hashes instalados, logins, flags), verifica igualdade exata com essa declaração
e recusa qualquer diferença, incluindo versões superiores. A declaração fica
ligada às migrações publicadas pelo mesmo ficheiro e digest, para não apontar
para algo que não existe. Usa a ferramenta cuja expectativa corresponde a esse
estado; código de uma fase futura só corre depois de essa fase acontecer. Se a
CI só prova o estado final, a conclusão dela não cobre operações intermédias.

## Entrada interativa e sessões longas

- **Pedir valores por terminal dentro de `sudo bash <<'BASH'`** com
  `</dev/tty` pode deixar o processo suspenso pelo sistema (estado `T` no `ps`),
  sem responder a `Ctrl+C`, porque deixa de ser o grupo em primeiro plano do
  terminal que o `sudo` criou. Verifica hashes num bloco e corre o passo
  interativo diretamente (`sudo /usr/bin/python3 -I -B <helper> <ação>`), ou lê os
  valores de um ficheiro protegido preparado pelo operador. Um processo parado
  antes de qualquer escrita termina-se com `kill -KILL` pelo PID; confirma no
  código que os valores eram todos pedidos antes de escrever.
- **Linhas coladas num terminal em modo canónico** são cortadas por volta dos
  4096 bytes. Um JSON grande (por exemplo um JWKS com certificados) chega
  truncado e falha a validação. Reduz ao necessário (só as chaves públicas),
  confirma o tamanho antes de colar, ou passa-o por ficheiro ou URL verificado.
- **Passos que bloqueiam durante muito tempo** (um build de uma hora num
  `systemctl start` de um serviço oneshot) correm dentro de `tmux` ou
  equivalente: uma queda de SSH mata o cliente a meio e o rollback automático
  não corre. Para recolher output longo: `tmux capture-pane -pS -3000 > ficheiro`.

## Diagnóstico que sobrevive à falha

- Um helper que captura o output do comando e só emite o código de saída perde a
  causa. Guarda o stderr filtrado por uma lista de mensagens estáticas aprovadas
  (o resto fica `[REDACTED]`), os SQLSTATE, a fase com nome próprio, a classe e
  os frames (ficheiro, função, linha) das exceções. Nunca argv, stdout de
  comandos que falharam, DSNs ou mensagens de exceção.
- Se o rollback falhar dentro do tratamento de um erro, regista os dois e
  relança o original. A 20/10 o rollback falhou e a exceção foi descartada; o
  subpasso exato nunca foi recuperado.
- Uma fase global que fica com o valor por omissão quando o chamador não a
  atualiza aponta para o sítio errado. Dá nome a cada passo e subpasso.
- Acrescenta diagnóstico com uma biblioteca comum, não reescrevendo o código
  revisto por geração automática: uma instrumentação assim produziu um diff de
  112 KB, apagou os comentários e obrigou a provar equivalência retirando a
  instrumentação e comparando a AST com a versão revista.
- Um filtro que oculta todas as linhas cumpriu o seu papel, mas não explica a
  falha. Nesse caso, uma sonda só de leitura que imprime apenas categorias
  (porta, variante, classe do erro, frases conhecidas) encontra a causa sem
  expor segredos.

## Retomar sem helpers improvisados

Depois de uma falha a meio, desenha a retoma no próprio procedimento: revalida o
estado atual, prova que os passos já feitos estão completos e continua a partir
do último passo verificado. Sem isso, cada falha obriga a escrever e rever um
helper novo de conclusão sob pressão, com o mesmo risco de erro que causou a
falha.

Se o trabalho se repete, promove o helper a procedimento versionado e testado
no repositório de infraestrutura, com parâmetros verificados.

## Coordenação

Quando deploys automáticos possam alterar o mesmo alvo, evita concorrência
com um mecanismo aprovado (freeze de merges, pausa do deploy, lock operacional
ou equivalente). Não exige freeze de repositórios sem relação com o alvo.
O operador revê o resultado de cada bloco antes de continuar; silêncio ou um
processo desaparecido não provam conclusão.

Referência técnica para o exemplo de catch-up: [systemd.timer — Persistent](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html#Persistent=), consultada em 19/10/2026; outros schedulers exigem verificar o seu próprio contrato.
