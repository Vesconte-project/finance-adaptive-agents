# Catálogo de padrões de falha

Cada entrada descreve um sintoma, uma causa possível, uma sonda e uma correção
proposta. São exemplos dependentes do ambiente, não instruções universais; a
proveniência de cada caso não é estabelecida por este catálogo.

## systemd

### `sudo` recusa-se dentro de uma unit endurecida
- **Sintoma:** `sudo: The "no new privileges" flag is set, which prevents sudo from running as root.`
- **Causa:** `NoNewPrivileges=true` na unit. O kernel ignora o bit setuid, e o `sudo` depende dele.
- **Sonda:** `setpriv --no-new-privs sudo -n -l`
- **Correção:** não uses `sudo` a partir de uma unit endurecida. Passa o pedido por D-Bus (`systemctl start`) autorizado por polkit, e faz o trabalho privilegiado numa unit root separada. O sandbox mantém-se intacto.

### Root dentro de uma unit não consegue escrever
- **Sintoma:** o processo corre como root e mesmo assim recebe `Read-only file system` ou `Permission denied`.
- **Causa:** uma proteção efetivamente aplicada pela unit ou pelo namespace pode tornar o caminho read-only, incluindo para processos root. Não atribuas a recusa a uma diretiva sem verificar a configuração ativa e o mount namespace. `ReadWritePaths=` pode permitir exceções graváveis dentro das proteções aplicáveis; não é, por si só, causa de bloqueio.
- **Sonda:** se a unit estiver ativa e a inspeção for autorizada, consulta a configuração efetiva e o namespace do processo sem alterar ficheiros: `pid=$(systemctl show UNIT -p MainPID --value); findmnt --task "$pid" --target /srv -o TARGET,OPTIONS`. Se não houver processo ativo, inspeciona a configuração aplicável; não inicies uma unit apenas para sondar.
- **Correção:** o trabalho privilegiado corre numa unit própria, fora do sandbox de quem o pede.

### Parar um serviço para outros sem avisar
- **Sintoma:** depois de reiniciar o serviço A, os serviços B e C ficaram parados e ninguém reparou.
- **Causa:** uma dependência aplicável pode propagar o *stop*; confirma a diretiva efetiva (por exemplo, `Requires=`) antes de atribuir o comportamento a esse mecanismo. O *start* de A pode não repor os dependentes.
- **Sonda:** `systemctl list-dependencies --reverse --plain A` identifica relações; inspeciona as units relevantes para confirmar se a relação é `Requires=` e se propaga o *stop* na versão instalada.
- **Correção:** antes do stop, registar que dependentes estavam ativos; depois do start, arrancá-los e exigir prova de que voltaram (não só `is-active`).

### Unit instalada diferente da do repositório
- **Sintoma:** um PR "endurece" uma unit e na verdade remove hardening que já lá estava.
- **Causa:** o autor partiu do ficheiro do repo, que estava desatualizado.
- **Sonda:** comparação de `sha256sum` entre repo e `/etc/systemd/system`.
- **Correção:** o repositório passa a ser a verdade **depois** de uma reconciliação explícita, nunca antes.

## Git

### `dubious ownership`
- **Sintoma:** `fatal: detected dubious ownership in repository at '...'`
- **Causa:** o processo corre com um utilizador diferente do dono do repositório; isto pode ocorrer quando código de uma release (dona: identidade de deploy) é executado com a identidade do serviço.
- **Sonda:** `runuser -u OUTRO -- git -C /caminho rev-parse HEAD`
- **Correção:** só considerar `safe.directory` depois de confirmar que o repositório e o código nele são confiáveis e que o caminho é o esperado para esse serviço. A opção contorna uma proteção do Git; não verifica a integridade nem torna seguro um repositório não confiável. Se essa confiança não puder ser estabelecida, não a apliques.

## Python e empacotamento

### Scripts da venv com shebang para um diretório que já não existe
- **Sintoma:** `bad interpreter: No such file or directory` em CLIs instalados dentro de uma release.
- **Causa:** a release foi construída num diretório de staging e depois renomeada. Os console scripts guardam o caminho absoluto do staging.
- **Sonda:** `head -1 release/.venv/bin/CLI` e confirmar que o interpretador existe.
- **Correção:** só executar código da release como root depois de verificar a sua origem e integridade e de confirmar que os ficheiros e diretórios são controlados por uma identidade confiável. `python3 -I` reduz influências do ambiente, mas não prova que o código seja confiável. Corrige o processo de build/instalação do launcher apenas após confirmar a cadeia de confiança.

### `python3 script.py` como root a partir de um diretório do utilizador
- **Sintoma:** nenhum, até alguém aproveitar.
- **Causa:** `sys.path[0]` é o diretório do script; um ficheiro com nome de módulo da biblioteca padrão é carregado primeiro.
- **Correção:** primeiro confirma a origem e integridade do commit e que a cópia root-owned não pode ser alterada por utilizadores não confiáveis. Só então considera `python3 -I` como defesa adicional; o modo isolado não torna código não confiável seguro.

## Heartbeat e execução de workers (comportamento depende do backend)

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
- **Sonda:** se o operador autorizar o contacto remoto, executa `runuser -u NOVA -- env HOME=... GIT_SSH_COMMAND="ssh -F .../config" git ls-remote REPOSITORY HEAD` para **cada** repositório distinto nos pull steps.
- **Correção:** usar aliases explícitos por repositório também nos pull steps.

### Runs Prefect presas em RUNNING sem processo
- **Sintoma:** runs `RUNNING` com meses, a bloquear janelas de manutenção e possivelmente limites de concorrência.
- **Causa:** o worker morreu sem transição de estado.
- **Correção:** apenas num backend Prefect e numa versão que suporte esta operação, e com autorização explícita do operador. Confirma que o run identificado não tem worker/processo ativo nem estado necessário para recuperação; fecha só o ID exato, nunca em bloco. Se backend, estado ou autorização forem incertos, não feches o run.

## Serviços que escrevem onde não devem

### Possível escrita dentro da release
- **Sintoma:** o serviço continua ativo, mas uma funcionalidade como um dashboard devolve 404 ou falha depois de tentar escrever.
- **Causa:** uma possibilidade é a aplicação tentar criar estado ou artefactos dentro do pacote instalado; um 404, por si só, não confirma essa hipótese.
- **Sonda:** com acesso autorizado, inspeciona localmente o erro/traceback relevante nos logs e confirma a exceção e o caminho da escrita que falhou. Compara esse caminho, sem expor valores ou linhas sensíveis, com a raiz da release e com o diretório de estado configurado por um diagnóstico seguro e específico da aplicação. Não uses apenas `/api/health` como prova.
- **Correção:** só se a sonda confirmar que a aplicação escreve indevidamente dentro da release, propõe apontar essa escrita para um diretório de estado autorizado e configurado; não alteres a configuração sem aprovação.

### Caminho antigo guardado nas definições do orquestrador
- **Sintoma:** depois de mudar a identidade de um worker, todos os trabalhos falham em 0–2 segundos com `PermissionError` num caminho que ninguém encontra na configuração do host.
- **Causa:** as definições de deployment, guardadas na base de dados do orquestrador, fixam variáveis de ambiente (aqui um diretório de cache) que se sobrepõem às da unit. O caminho antigo era acessível à identidade anterior e deixou de o ser.
- **Sonda:** se o backend e o endpoint forem confirmados e a consulta estiver autorizada, inspeciona apenas as chaves relevantes de `job_variables.env`; compara com os nomes disponíveis no ambiente do processo. Não imprimas dumps de ambiente nem valores de credenciais; mascara qualquer valor necessário para a comparação.
- **Correção:** tirar o valor das definições e deixar a unit fornecê-lo; republicar. Não relaxar permissões do caminho antigo para o fazer funcionar.

### Um pai sem permissão de travessia trava um symlink correto
- **Sintoma:** um caminho aponta para o sítio certo e o acesso falha à mesma.
- **Causa:** para atravessar um caminho é precisa permissão de execução em todos os diretórios acima. Um `0750` pertencente a outra identidade chega para bloquear.
- **Sonda:** `sudo -u IDENTIDADE test -x /cada/diretório/acima`.
- **Correção:** só alterar permissões depois de confirmar o caminho, os proprietários, os consumidores e a política de menor privilégio do host. Um modo como `0711` pode ser uma opção para um ancestral partilhado, mas não é universal; propõe a alteração mínima que permita a travessia sem conceder leitura desnecessária.

## Guardas e credenciais

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
- **Sonda:** com autorização para inspecionar a identidade do serviço, identifica as fontes reais e calcula primeiro fingerprints das chaves públicas (`ssh-keygen -lf PUBLIC_KEY`). Se for necessário ler uma chave privada para obter a chave pública/fingerprint, exige autorização explícita para essa leitura; nunca mostres o conteúdo privado.
- **Correção:** só alterar o fornecedor remoto com autorização explícita. Antes de registar a chave, confirma pelo fingerprint que é a chave de serviço pretendida e limita as permissões ao necessário. Nunca mostres nem copies o conteúdo privado.
