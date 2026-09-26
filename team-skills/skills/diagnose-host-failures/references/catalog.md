# Catálogo de falhas reais

Cada entrada: sintoma exato, causa, sonda que o confirma, e a correção certa.
Todas aconteceram numa migração real de um servidor de produção.

## systemd

### `sudo` recusa-se dentro de uma unit endurecida
- **Sintoma:** `sudo: The "no new privileges" flag is set, which prevents sudo from running as root.`
- **Causa:** `NoNewPrivileges=true` na unit. O kernel ignora o bit setuid, e o `sudo` depende dele.
- **Sonda:** `setpriv --no-new-privs sudo -n -l`
- **Correção:** não uses `sudo` a partir de uma unit endurecida. Passa o pedido por D-Bus (`systemctl start`) autorizado por polkit, e faz o trabalho privilegiado numa unit root separada. O sandbox mantém-se intacto.

### Root dentro de uma unit não consegue escrever
- **Sintoma:** o processo corre como root e mesmo assim recebe `Read-only file system` ou `Permission denied`.
- **Causa:** `ProtectSystem=strict` (ou `ProtectHome`, `ReadWritePaths`) aplica-se a **todos** os processos da unit, incluindo os filhos root.
- **Sonda:** ler a unit; confirmar com `systemd-run -p ProtectSystem=strict --pipe touch /srv/x`.
- **Correção:** o trabalho privilegiado corre numa unit própria, fora do sandbox de quem o pede.

### Parar um serviço para outros sem avisar
- **Sintoma:** depois de reiniciar o serviço A, os serviços B e C ficaram parados e ninguém reparou.
- **Causa:** B e C têm `Requires=A`. O *stop* propaga-se; o *start* de A não os repõe.
- **Sonda:** `systemctl list-dependencies --reverse --plain A`
- **Correção:** antes do stop, registar que dependentes estavam ativos; depois do start, arrancá-los e exigir prova de que voltaram (não só `is-active`).

### Unit instalada diferente da do repositório
- **Sintoma:** um PR "endurece" uma unit e na verdade remove hardening que já lá estava.
- **Causa:** o autor partiu do ficheiro do repo, que estava desatualizado.
- **Sonda:** comparação de `sha256sum` entre repo e `/etc/systemd/system`.
- **Correção:** o repositório passa a ser a verdade **depois** de uma reconciliação explícita, nunca antes.

## Git

### `dubious ownership`
- **Sintoma:** `fatal: detected dubious ownership in repository at '...'`
- **Causa:** o processo corre com um utilizador diferente do dono do repositório. Acontece sempre que se executa código de uma release (dona: identidade de deploy) com a identidade do serviço.
- **Sonda:** `runuser -u OUTRO -- git -C /caminho rev-parse HEAD`
- **Correção:** passar `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory GIT_CONFIG_VALUE_0=/caminho` ao processo. Não mexer no `~/.gitconfig` global.

### Chave de deploy com escrita onde não devia
- **Sintoma:** um script copia uma chave SSH para a identidade que constrói releases.
- **Causa:** as chaves de deploy do GitHub podem ser de leitura ou de escrita, e o nome não distingue.
- **Sonda:** `GIT_SSH_COMMAND="ssh -i CHAVE -o IdentitiesOnly=yes" git push --dry-run REPO HEAD:refs/heads/probe-nunca-criada` — recusa significa leitura apenas; `ls-remote` confirma que a chave funciona.
- **Correção:** a identidade que executa código de build (instala dependências) nunca recebe credencial de escrita. Um `uv sync` executa código arbitrário de terceiros.

## Python e empacotamento

### Scripts da venv com shebang para um diretório que já não existe
- **Sintoma:** `bad interpreter: No such file or directory` em CLIs instalados dentro de uma release.
- **Causa:** a release foi construída num diretório de staging e depois renomeada. Os console scripts guardam o caminho absoluto do staging.
- **Sonda:** `head -1 release/.venv/bin/CLI` e confirmar que o interpretador existe.
- **Correção:** reescrever os shebangs depois do rename, ou gerar launchers próprios que resolvam o caminho em runtime.

### `python3 script.py` como root a partir de um diretório do utilizador
- **Sintoma:** nenhum, até alguém aproveitar.
- **Causa:** `sys.path[0]` é o diretório do script; um ficheiro com nome de módulo da biblioteca padrão é carregado primeiro.
- **Correção:** `python3 -I`, e correr sempre a partir de uma cópia root-owned exportada de um commit verificado.

## Prefect (aplica-se a qualquer worker com heartbeat)

### Readiness que aceita o worker antigo
- **Sintoma:** ativação "verificada" em 0,34 s; uma release partida passaria.
- **Causa:** o registo do worker anterior, com o mesmo nome, continua `ONLINE` durante cerca de 90 s depois do restart.
- **Sonda:** comparar `last_heartbeat_time` com o instante em que a ativação começou.
- **Correção:** exigir heartbeat posterior ao início da ativação. Regra geral: nunca aceitar como prova um estado que já era verdade antes da mudança.

### O SHA da release não é o código que corre
- **Sintoma:** `current/` aponta para uma release nova, mas os flows executam código antigo.
- **Causa:** os deployments clonam o código no momento da execução, fixados a um SHA publicado antes.
- **Sonda:** ler os `pull_steps` dos deployments e comparar com o SHA ativo.
- **Correção:** a publicação dos deployments faz parte da ativação, fixada ao SHA da release, e verificada depois.

### O clone do flow perde as credenciais ao mudar de identidade
- **Sintoma:** todos os flows falham no clone depois de um serviço mudar de utilizador.
- **Causa:** o pull step usa `git@github.com:...` e a identidade nova só tem aliases SSH configurados.
- **Sonda:** `runuser -u NOVA -- env HOME=... GIT_SSH_COMMAND="ssh -F .../config" git ls-remote REPOSITORY HEAD` para **cada** repositório distinto nos pull steps.
- **Correção:** usar aliases explícitos por repositório também nos pull steps.

### Runs presas em RUNNING sem processo
- **Sintoma:** runs `RUNNING` com meses, a bloquear janelas de manutenção e possivelmente limites de concorrência.
- **Causa:** o worker morreu sem transição de estado.
- **Correção:** fechar por ID exato, com `force`, depois de confirmar nome e hora, e nunca em bloco.

## Serviços que escrevem onde não devem

### Aplicação a tentar escrever dentro da release
- **Sintoma:** `Permission denied` ao arrancar; funcionalidade some sem o serviço falhar (no caso real, o dashboard do Prefect).
- **Causa:** o serviço quer criar diretórios dentro do próprio pacote instalado.
- **Sonda:** verificar no arranque o que o serviço oferece ao utilizador, não só `/api/health`.
- **Correção:** apontar essas escritas para um diretório de estado gravável, por configuração.

## Dados e agendamentos

### Trabalho diário que atravessa a meia-noite UTC
- **Sintoma:** uma etapa deixa de correr todos os dias, em silêncio, com um alerta "dados não prontos".
- **Causa:** a data de referência é calculada no momento da decisão, e não no início da execução. O flow começa às 23:10 e decide às 00:13.
- **Sonda:** procurar nos logs o alerta de "blocked/skipped" e comparar a data pedida com o watermark.
- **Correção:** fixar a data lógica no início da execução e passá-la adiante.

### Caminho antigo guardado nas definições do orquestrador
- **Sintoma:** depois de mudar a identidade de um worker, todos os trabalhos falham em 0–2 segundos com `PermissionError` num caminho que ninguém encontra na configuração do host.
- **Causa:** as definições de deployment, guardadas na base de dados do orquestrador, fixam variáveis de ambiente (aqui um diretório de cache) que se sobrepõem às da unit. O caminho antigo era acessível à identidade anterior e deixou de o ser.
- **Sonda:** ler `job_variables.env` de cada deployment pela API; comparar com o ambiente real do processo (`/proc/<pid>/environ`).
- **Correção:** tirar o valor das definições e deixar a unit fornecê-lo; republicar. Não relaxar permissões do caminho antigo para o fazer funcionar.

### Segredos em texto simples nas definições de deployment
- **Sintoma:** uma password de base de dados aparece ao consultar a API do orquestrador.
- **Causa:** o ficheiro de configuração referencia um cofre, mas a referência é resolvida na publicação e o valor final fica guardado na base do orquestrador.
- **Sonda:** procurar padrões de DSN e chaves com "password", "token" ou "secret" nas variáveis dos deployments — imprimindo só nomes.
- **Correção:** mover essas variáveis para o ficheiro de ambiente root-owned da unit, republicar, e **rodar** a credencial exposta.

### Um pai sem permissão de travessia trava um symlink correto
- **Sintoma:** um caminho aponta para o sítio certo e o acesso falha à mesma.
- **Causa:** para atravessar um caminho é precisa permissão de execução em todos os diretórios acima. Um `0750` pertencente a outra identidade chega para bloquear.
- **Sonda:** `sudo -u IDENTIDADE test -x /cada/diretório/acima`.
- **Correção:** tornar o ancestral partilhado atravessável (`root:root 0711`), mantendo cada filho privado. Não abrir o ancestral a leitura.

## Sinais para fora da máquina

### CI vermelho num deploy que funcionou como desenhado
- **Sintoma:** depois de instalar um gate de janela, um deploy legítimo aparece como falha no CI; no host não há nada partido.
- **Causa:** o validador sai com um código próprio para "adiado" (75), mas a unit não tem `SuccessExitStatus=`, logo fica `failed`; o cliente usa `check=True` e levanta; o step fica vermelho.
- **Sonda:** `systemctl show RELEASE_UNIT@COMPONENTE.service -p Result -p ExecMainStatus` e comparar com o código que o script devolve para adiamento.
- **Correção:** declarar `SuccessExitStatus=` na unit **e** o cliente imprimir "aceite/adiado" ou "feito". Só uma das duas não resolve. Depois, documentar que verde passou a significar "aceite", não "em produção".

### Deploy parcial silencioso depois de um adiamento
- **Sintoma:** um componente na versão nova e os restantes na antiga, do mesmo commit, sem nenhum erro visível.
- **Causa:** o workflow pedia N componentes em sequência num bloco de shell com `-e`; o adiamento do primeiro abortou o bloco e os seguintes nunca foram pedidos. O retry só conhece pedidos registados.
- **Sonda:** comparar o SHA fixado/instalado de cada componente do mesmo repositório; os pedidos pendentes no diretório de requests.
- **Correção:** registar todos os pedidos antes de qualquer gate poder interromper, e reportar estado agregado. Não confiar no retry para cobrir pedidos que nunca existiram.

### Ninguém sabe que o trabalho adiado acabou por entrar
- **Sintoma:** quem fez merge fica com a ideia de que falhou; o deploy entrou meia hora depois em silêncio.
- **Causa:** o canal de alerta só envia falhas. A conclusão não produz sinal nenhum fora da máquina.
- **Correção:** enviar sucesso e falha ao mesmo check de monitorização, para haver notificação nas transições e a cor refletir o último resultado real.

### Check de monitorização cinzento confundido com desativado
- **Sintoma:** um check recém-criado aparece cinzento; parece estar desligado.
- **Causa:** é o estado "new" — nunca recebeu ping. Num alarme explícito, que só recebe falhas, é o estado normal e permanente até haver um incidente.
- **Correção:** documentá-lo. E não configurar período curto num alarme explícito: ficaria "down" sozinho por silêncio.

### Um alarme explícito fica vermelho para sempre
- **Sintoma:** o check continua vermelho depois de o problema estar resolvido, e acumula lembretes.
- **Causa:** nada envia o sinal de recuperação: o mecanismo só sabe reportar falhas.
- **Correção:** documentar o comando de reset ao lado do de instalação, lendo o URL do ficheiro root-owned sem o imprimir: `sudo sh -c '. /etc/.../alert.env; curl -fsS "$URL_VAR"'`.

## Guardas e credenciais

### Um scanner de segredos que passa sem comparar nada
- **Sintoma:** `findings=0 result=PASS` num intervalo que contém material sensível; a verificação nunca disse NÃO desde que foi instalada.
- **Causa:** o extrator de segredos apanha `PermissionError` e faz `continue`. A identidade do serviço não consegue ler nenhum dos ficheiros de segredos configurados, todos `0600` de outro dono.
- **Sonda:** `systemctl show UNIT -p User --value`, `id IDENTIDADE`, e `stat -c '%a %U:%G %n'` de cada input declarado.
- **Correção:** falhar quando um input não abre **e** quando produz zero valores; uma fase privilegiada separada que emite um veredicto, em vez de baixar permissões. Exigir no output a contagem de inputs e de valores comparáveis.

### Deteção de segredos por sufixo do nome deixa passar nomes novos
- **Sintoma:** uma chave sensível não é detetada; a regra parece razoável.
- **Causa:** regra do tipo `(TOKEN|SECRET|PASSWORD|DATABASE_URL|DSN)$`. Escaparam, em casos reais, `PREFECT_API_DATABASE_CONNECTION_URL` e `DATA_OPS_ALERT_WEBHOOK_URL`.
- **Correção:** classificar explicitamente cada chave de cada input e falhar quando aparece uma chave sem classificação. O sufixo passa a conveniência.

### Unit transitória perde o InvocationID antes de a lerem
- **Sintoma:** `systemctl show UNIT -p InvocationID --value` devolve vazio logo depois de a unit ter corrido, e a verificação que depende dele recusa.
- **Causa:** uma `Type=oneshot` em `/run/systemd/system` que ninguém referencia é descarregada ao ficar inativa e perde o estado de execução. Units normais mantêm-no porque um timer as referencia.
- **Sonda:** comparar com uma unit referenciada por timer — essa mantém o ID depois de `inactive` ou `failed`.
- **Correção:** `RemainAfterExit=yes`, e a ordem arrancar → ler o ID → verificar o journal → `stop` → remover → `daemon-reload`.

### Dois lotes tocam no mesmo ficheiro e o segundo recusa
- **Sintoma:** `baseline drift` num lote cujo alvo já está instalado e correto.
- **Causa:** os dois lotes foram integrados no ramo principal antes de qualquer um ser aplicado; o primeiro fez `stage` de uma fonte que já continha o segundo, e instalou o conteúdo final. O baseline do segundo descreve um estado intermédio que nunca existiu.
- **Sonda:** comparar o hash instalado com o da fonte staged **e** com o do commit em que só o primeiro lote existia.
- **Correção:** o lote distingue três casos — igual ao baseline (instala), igual ao alvo (registra no-op, sem escrever nada), outra coisa (recusa).

### Apagar uma deploy key "duplicada" parte o clone em runtime
- **Sintoma:** deploy falha com `ls-remote ... exit status 128`; o serviço vivo continua a funcionar mas **não pode ser reiniciado**, porque o arranque valida o acesso ao repositório.
- **Causa:** das duas chaves de leitura, uma era da identidade de serviço. Só se nota no próximo clone, que pode ser horas depois.
- **Sonda:** mapear todas as chaves por **fingerprint** (`ssh-keygen -lf`), em `~/.ssh`, em `/var/lib/*/.ssh` e em `/etc/<projeto>/*ssh*/`.
- **Correção:** recuperar a pública a partir da privada que continua no host (`ssh-keygen -y -f privada`) e voltar a registá-la só-leitura. Apagar o registo remoto não destrói nada local.

### Ligar escrita a uma chave partilhada dá escrita ao orquestrador
- **Sintoma:** nenhum — é uma porta aberta, não uma falha.
- **Causa:** a mesma chave privada serve a conta humana e a identidade que corre os workers. Ligar-lhe escrita para publicares dá escrita a código que corre dentro de qualquer trabalho agendado, no mesmo ramo que o validador de deploys aceita como verdade.
- **Sonda:** comparar fingerprints das chaves da conta humana com as da identidade de serviço; confirmar com um `push --dry-run` executado **como** o serviço.
- **Correção:** chave própria por identidade, só-leitura no runtime. Adicionar a nova de escrita **antes** de retirar a escrita à partilhada.
