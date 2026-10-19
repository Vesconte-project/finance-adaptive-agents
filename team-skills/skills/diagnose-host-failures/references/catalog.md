# Catálogo de padrões de falha

Cada entrada descreve um sintoma, uma causa possível, uma sonda e uma correção
proposta. São exemplos dependentes do ambiente, não instruções universais; a
proveniência de cada caso não é estabelecida por este catálogo.

## systemd

### `sudo` recusa-se dentro de uma unit endurecida
- **Sintoma:** `sudo: The "no new privileges" flag is set, which prevents sudo from running as root.`
- **Causa possível:** `NoNewPrivileges=true` na unit. O kernel ignora o bit setuid, e o `sudo` depende dele.
- **Sonda:** `setpriv --no-new-privs sudo -n -l`, apenas se a invocação de sudo estiver autorizada; pode gerar eventos nos logs de autenticação.
- **Correção:** não uses `sudo` a partir de uma unit endurecida. Passa o pedido por D-Bus (`systemctl start`) autorizado por polkit, e faz o trabalho privilegiado numa unit root separada. O sandbox mantém-se intacto.

### Root dentro de uma unit não consegue escrever
- **Sintoma:** o processo corre como root e mesmo assim recebe `Read-only file system` ou `Permission denied`.
- **Causa possível:** uma proteção efetivamente aplicada pela unit ou pelo namespace pode tornar o caminho read-only, incluindo para processos root. Não atribuas a recusa a uma diretiva sem verificar a configuração ativa e o mount namespace. `ReadWritePaths=` pode permitir exceções graváveis dentro das proteções aplicáveis; não é, por si só, causa de bloqueio.
- **Sonda:** se a unit estiver ativa e a inspeção for autorizada, consulta a configuração efetiva e o namespace do processo sem alterar ficheiros: `pid=$(systemctl show UNIT -p MainPID --value); findmnt --task "$pid" --target /srv -o TARGET,OPTIONS`. Se não houver processo ativo, inspeciona a configuração aplicável; não inicies uma unit apenas para sondar.
- **Correção:** o trabalho privilegiado corre numa unit própria, fora do sandbox de quem o pede.

### Parar um serviço para outros sem avisar
- **Pré-condição:** systemd com B/C a dependerem de A; distingue os comandos e jobs realmente executados.
- **Sintoma:** depois de parar A e mais tarde arrancar A num comando separado, B/C continuam parados.
- **Causa possível:** se B tem `Requires=A`, parar explicitamente A também pode parar B; arrancar A depois não implica arrancar os seus dependentes inversos. Isto difere de um `restart` explícito de A, que propaga restart aos dependentes com `Requires=` segundo o contrato documentado. Outras diretivas e modos de job podem mudar o resultado; não atribuas uma falha após `restart` a um simples stop/start sem conferir os jobs.
- **Sonda:** consulta o journal e a operação exata; `systemctl list-dependencies --reverse --plain A` ajuda a localizar relações carregadas, mas não substitui verificar as diretivas efetivas de cada unit e a documentação instalada.
- **Correção:** para um stop/start aprovado, regista dependentes ativos antes do stop e prevê a sua reposição autorizada. Verifica instância e funcionamento depois; `is-active` sozinho não prova recuperação.

### Unit instalada diferente da do repositório
- **Sintoma:** um PR "endurece" uma unit e na verdade remove hardening que já lá estava.
- **Causa possível:** o autor partiu do ficheiro do repo, que estava desatualizado.
- **Sonda:** comparação de `sha256sum` entre repo e `/etc/systemd/system`.
- **Correção:** o repositório passa a ser a verdade **depois** de uma reconciliação explícita, nunca antes.

## Git

### `dubious ownership`
- **Sintoma:** `fatal: detected dubious ownership in repository at '...'`
- **Causa possível:** o processo corre com um utilizador diferente do dono do repositório; isto pode ocorrer quando código de uma release (dona: identidade de deploy) é executado com a identidade do serviço.
- **Sonda:** `runuser -u OUTRO -- git -C /caminho rev-parse HEAD`
- **Correção:** só considerar `safe.directory` depois de confirmar que o repositório e o código nele são confiáveis e que o caminho é o esperado para esse serviço. A opção contorna uma proteção do Git; não verifica a integridade nem torna seguro um repositório não confiável. Se essa confiança não puder ser estabelecida, não a apliques.

## Python e empacotamento

### Scripts da venv com shebang para um diretório que já não existe
- **Sintoma:** `bad interpreter: No such file or directory` em CLIs instalados dentro de uma release.
- **Causa possível:** a release foi construída num diretório de staging e depois renomeada. Os console scripts guardam o caminho absoluto do staging.
- **Sonda:** `head -1 release/.venv/bin/CLI` e confirmar que o interpretador existe.
- **Correção:** só executar código da release como root depois de verificar a sua origem e integridade e de confirmar que os ficheiros e diretórios são controlados por uma identidade confiável. `python3 -I` reduz influências do ambiente, mas não prova que o código seja confiável. Corrige o processo de build/instalação do launcher apenas após confirmar a cadeia de confiança: cria/recria a venv no caminho final a partir das dependências verificadas, em vez de mover uma venv presumindo relocabilidade ou corrigir só um shebang. Se a ferramenta produzir artefactos relocáveis, valida o seu contrato específico. Verifica o shebang e uma invocação de diagnóstico sem efeitos antes de ativar.

### `python3 script.py` como root a partir de um diretório do utilizador
- **Sintoma:** nenhum, até alguém aproveitar.
- **Causa possível:** `sys.path[0]` é o diretório do script; um ficheiro com nome de módulo da biblioteca padrão é carregado primeiro.
- **Correção:** primeiro confirma a origem e integridade do commit e que a cópia root-owned não pode ser alterada por utilizadores não confiáveis. Só então considera `python3 -I` como defesa adicional; o modo isolado não torna código não confiável seguro.

## Heartbeat e execução de workers (comportamento depende do backend)

### Readiness que aceita o worker antigo
- **Sintoma:** ativação "verificada" em 0,34 s; uma release partida passaria.
- **Causa possível:** no caso observado, um registo do worker anterior, com o mesmo nome, continuava `ONLINE` durante cerca de 90 s; essa duração não é um contrato do backend.
- **Sonda:** regista a nova instância (identidade única do worker, PID com instante de início e invocação do serviço) e o SHA/artefacto esperado. Um heartbeat posterior ao início da ativação pode ainda vir do processo antigo; até um nome reutilizado com timestamp recente não identifica o emissor.
- **Correção:** exige um heartbeat fresco associado inequivocamente à nova instância e evidência de que essa instância carregou a release esperada. Se o backend só expõe um nome reutilizado, corrobora com logs da nova invocação e prova que a anterior não pode emitir, ou declara a ativação não verificada. Não confundir worker pronto com sucesso de um flow.

### O SHA da release não é o código que corre
- **Pré-condição:** backend com deployments e pull steps Git em runtime (como Prefect); no relato, `current/` era um symlink de releases. Noutro layout compara o identificador ativo equivalente.
- **Sintoma:** `current/` aponta para uma release nova, mas os flows executam código antigo.
- **Causa possível:** os deployments clonam o código no momento da execução, fixados a um SHA publicado antes.
- **Sonda:** ler os `pull_steps` dos deployments e comparar com o SHA ativo.
- **Correção:** a publicação dos deployments faz parte da ativação, fixada ao SHA da release, e verificada depois.

### O clone do flow perde as credenciais ao mudar de identidade
- **Pré-condição:** flows com pull steps Git por SSH e configuração por identidade; o relato usava GitHub e aliases SSH, que não se presumem noutro host.
- **Sintoma:** todos os flows falham no clone depois de um serviço mudar de utilizador.
- **Causa possível:** o pull step usa `git@github.com:...` e a identidade nova só tem aliases SSH configurados.
- **Sonda:** se o operador autorizar o contacto remoto, executa `runuser -u NOVA -- env HOME=... GIT_SSH_COMMAND="ssh -F .../config" git ls-remote REPOSITORY HEAD` para **cada** repositório distinto nos pull steps.
- **Correção:** usar aliases explícitos por repositório também nos pull steps.

### Runs Prefect presas em RUNNING sem processo
- **Pré-condição:** backend Prefect e versão/API confirmados; não aplicar transições Prefect a outro orquestrador.
- **Sintoma:** runs `RUNNING` com meses, a bloquear janelas de manutenção e possivelmente limites de concorrência.
- **Causa possível:** o worker morreu sem transição de estado.
- **Correção:** apenas num backend Prefect e numa versão que suporte esta operação, e com autorização explícita do operador. Confirma que o run identificado não tem worker/processo ativo nem estado necessário para recuperação; fecha só o ID exato, nunca em bloco. Se backend, estado ou autorização forem incertos, não feches o run.

## Serviços que escrevem onde não devem

### Possível escrita dentro da release
- **Sintoma:** o serviço continua ativo, mas uma funcionalidade como um dashboard devolve 404 ou falha depois de tentar escrever.
- **Causa possível:** uma possibilidade é a aplicação tentar criar estado ou artefactos dentro do pacote instalado; um 404, por si só, não confirma essa hipótese.
- **Sonda:** com acesso autorizado, inspeciona localmente o erro/traceback relevante nos logs e confirma a exceção e o caminho da escrita que falhou. Compara esse caminho, sem expor valores ou linhas sensíveis, com a raiz da release e com o diretório de estado configurado por um diagnóstico seguro e específico da aplicação. Não uses apenas `/api/health` como prova.
- **Correção:** só se a sonda confirmar que a aplicação escreve indevidamente dentro da release, propõe apontar essa escrita para um diretório de estado autorizado e configurado; não alteres a configuração sem aprovação.

### Caminho antigo guardado nas definições do orquestrador
- **Pré-condição:** backend com ambiente por deployment/run (por exemplo `job_variables.env` em Prefect), template e precedência efetivos confirmados.
- **Sintoma:** depois de mudar a identidade de um worker, todos os trabalhos falham em 0–2 segundos com `PermissionError` num caminho que ninguém encontra na configuração do host.
- **Causa possível:** as definições de deployment, guardadas na base de dados do orquestrador, podem fixar variáveis de ambiente; no relato, um diretório de cache prevalecia sobre a unit. Confirma a precedência na template/worker e no subprocesso real antes de concluir. O caminho antigo era acessível à identidade anterior e deixou de o ser.
- **Sonda:** se o backend e o endpoint forem confirmados e a consulta estiver autorizada, inspeciona apenas as chaves relevantes de `job_variables.env`; compara com os nomes disponíveis no ambiente do processo. Não imprimas dumps de ambiente nem valores de credenciais; mascara qualquer valor necessário para a comparação.
- **Correção:** tirar o valor das definições e deixar a unit fornecê-lo; republicar. Não relaxar permissões do caminho antigo para o fazer funcionar.

### Uma password aparece na API do orquestrador
- **Pré-condição:** backend com publicação de deployments/configuração e referências a cofre ou variáveis resolvidas nessa publicação; confirma formato, versão e controlo de acesso da API.
- **Sintoma:** a configuração persistida/API expõe um valor de credencial onde se esperava uma referência protegida.
- **Causa possível:** no relato, a referência ao cofre foi resolvida pelo publicador e guardada em plaintext. Outra origem também é possível; presença numa API não prova quando nem por quem foi introduzida.
- **Sonda:** sob o acesso já autorizado, inspeciona apenas o campo relevante e o código/configuração de publicação, sem imprimir o valor nem dumps da API, logs ou ambiente. Prefere reproduzir a resolução com um marcador não secreto num ambiente descartável; confirma quem consegue ler o campo persistido.
- **Correção:** se confirmado, substitui o plaintext pelo mecanismo de injeção em runtime aprovado e suportado, preservando funcionalidade e recuperação. Avalia leitores e cópias históricas; roda a credencial se houve exposição não autorizada ou ela não puder ser excluída, dentro do âmbito aprovado. Apagar o campo atual não revoga uma credencial nem apaga todas as cópias.

### Um pai sem permissão de travessia trava um symlink correto
- **Sintoma:** um caminho aponta para o sítio certo e o acesso falha à mesma.
- **Causa possível:** para atravessar um caminho é precisa permissão de execução em todos os diretórios acima. Um `0750` pertencente a outra identidade chega para bloquear.
- **Sonda:** com autorização para executar sob outra identidade, `runuser -u IDENTIDADE -- test -x /cada/diretório/acima`; confirma os ancestrais relevantes, sem alargar privilégios para executar a sonda.
- **Correção:** só alterar permissões depois de confirmar o caminho, os proprietários, os consumidores e a política de menor privilégio do host. Um modo como `0711` pode ser uma opção para um ancestral partilhado, mas não é universal; propõe a alteração mínima que permita a travessia sem conceder leitura desnecessária.

## Guardas e credenciais

### Unit de prova perde o InvocationID antes de a lerem
- **Sintoma:** `systemctl show UNIT -p InvocationID --value` devolve vazio logo depois de a unit ter corrido, e a verificação que depende dele recusa.
- **Causa possível:** garbage collection pode descarregar configuração e estado quando a unit deixa de ser necessária. Um ficheiro em `/run/systemd/system` é uma unit de runtime, não prova de uma unit transitória criada por API.
- **Sonda:** verifica estado, referências, jobs e `CollectMode=` na versão instalada; não assumes que toda unit normal tem um timer nem que todo estado `failed` é retido. Preserva o journal e associa os eventos à invocação, não apenas ao nome.
- **Correção:** captura o ID enquanto a invocação é observável. Numa sonda oneshot adequada, `RemainAfterExit=yes` pode reter `active (exited)` após sucesso; implica que outro `start` não repete a execução até um `stop` apropriado. Valida esse efeito e o plano de limpeza: recolher/verificar evidência, parar a sonda, remover apenas os seus artefactos e recarregar a configuração. Sem ID inequívoco, não declarar a verificação concluída.

### Dois lotes tocam no mesmo ficheiro e o segundo recusa
- **Sintoma:** `baseline drift` num lote cujo alvo já está instalado e correto.
- **Pré-condição:** instalador de ficheiros que compara o hash instalado com uma linha de base esperada e prepara fonte de um ramo integrado. Aqui “lote” significa um conjunto aprovado de alterações e `stage` a sua preparação imutável; `baseline drift` é a recusa quando o instalado difere do esperado. Só aplica o exemplo se existir esse mecanismo; valida o delta autorizado antes de aceitar instalação ou no-op.
- **Causa possível:** os dois lotes foram integrados no ramo principal antes de qualquer um ser aplicado; o primeiro fez `stage` de uma fonte que já continha o segundo, e instalou o conteúdo final. O baseline do segundo descreve um estado intermédio que nunca existiu.
- **Sonda:** comparar o hash instalado com o da fonte staged **e** com o do commit em que só o primeiro lote existia.
- **Correção:** o lote distingue três casos — igual ao baseline (instala), igual ao alvo (registra no-op, sem escrever nada), outra coisa (recusa).

### Apagar uma deploy key "duplicada" parte o clone em runtime
- **Pré-condição:** serviço que clona ou valida o acesso ao repositório no arranque; confirma esse comportamento e as identidades envolvidas.
- **Sintoma:** `ls-remote ... exit status 128` após alteração do inventário de chaves; o processo vivo pode continuar, mas o próximo arranque pode falhar se depender desse acesso.
- **Causa possível:** uma chave removida como duplicada ainda era usada pela identidade do serviço. No relato havia duas chaves de leitura, uma do serviço; esse inventário não se presume noutro alvo. A falha pode só surgir no clone seguinte.
- **Sonda:** com autorização para inspecionar a identidade do serviço, identifica as fontes reais e calcula primeiro fingerprints das chaves públicas (`ssh-keygen -lf PUBLIC_KEY`). Se for necessário ler uma chave privada para obter a chave pública/fingerprint, exige autorização explícita para essa leitura; nunca mostres o conteúdo privado.
- **Correção:** só alterar o fornecedor remoto com autorização explícita. Antes de registar a chave, confirma pelo fingerprint que é a chave de serviço pretendida e limita as permissões ao necessário. Nunca mostres nem copies o conteúdo privado.

## Fontes para as correções de lifecycle

Consultadas em 19/10/2026; confirma a documentação da versão instalada: [systemd.unit — garbage collection](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html#Unit%20Garbage%20Collection) e [systemd.service — RemainAfterExit](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html#RemainAfterExit=). Os exemplos de workers continuam a depender do contrato do backend real.

Para entrypoints Python, a [documentação de venv](https://docs.python.org/3/library/venv.html#how-venvs-work) explica os shebangs absolutos e a falta de relocabilidade geral (consultada em 19/10/2026).

Correção de dependências conferida em 20/10/2026: [systemd.unit — Requires](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html#Requires=), distinguindo restart explícito de stop/start separados.
