# Provar o artefacto entregue e quem o consome

## Checkout não é pacote instalado

Quando a instalação produz um arquivo, testa a cadeia que chega ao operador:
fonte fixada → empacotamento → extração pelas regras reais → admissão/construtor
→ ação de instalação → verificação do consumidor. Não extraias com permissões ou
tratamento de links mais permissivos apenas para fazer a prova passar.

Num caso relatado, o arquivo só transportava ficheiros regulares. Clones cujas
refs estavam empacotadas perderam diretórios Git vazios necessários; os ficheiros
estavam presentes, mas a admissão deixou de reconhecer os repositórios extraídos.
Uma prova no checkout não exercitava essa transformação.

Se o formato precisa de metadados Git, prova-o com as refs empacotadas e o arquivo
real. Se o formato não precisa de Git, não acrescentes .git para imitar o caso.
Diretórios necessários devem ser representados pelo contrato ou criados por uma
regra estreita e validada; não afrouxes a segurança da extração para os recuperar.

Usa o mesmo digest de pacote na prova e na proposta de instalação. Regista as
versões e dimensões não reproduzidas; testes verdes de módulos não são prova do
arquivo final.

## O acesso inclui os ancestrais e a identidade efetiva

Um recibo regular root-owned 0644 continua ilegível para um serviço se um dos
diretórios anteriores for 0700 de outra identidade. Verificar apenas o ficheiro
ou conseguir lê-lo como root não prova o consumo.

Inventaria dono/grupo/modo dos ancestrais e prova a leitura/parsing no contexto
relevante do consumidor: UID/GID e grupos suplementares, sandbox, namespace de
mounts e origem da configuração. No teste negativo, conserva o ficheiro legível
e bloqueia só um ancestral. Não uses root para afirmar esse resultado.

Se o recibo é metadado público mas a pasta anterior contém estado privado,
avalia uma localização separada, com ownership/mode e escrita controlada. Não
alargues a pasta privada apenas para satisfazer a sonda; a alternativa depende
do âmbito aprovado. Não copies segredos para um recibo público.

## Entry point e serviço real

Para um Postgres descartável, imagem/digest corretos não chegam se entrypoint,
porta, socket, HBA ou utilizador diferirem da unit alvo. Testa esse arranque e a
autenticação com a configuração efetiva e dados sintéticos. Se o PGDATA parcial
já existe, arranque, adoção e recuperação são operações distintas de inicializar;
não apagues nem reinicializes para fazer a prova passar.

Uma fronteira de systemd/PID1 exige ambiente descartável capaz de a exercitar,
com autorização e isolamento apropriados. Um contentor Python sem systemd prova
a lógica ou o texto da unit, não a aplicação das propriedades por PID1.

## Proveniência e limite

Arquivo Git, arranque da scratch e travessia do recibo ocorreram na instalação
[ENG-259](https://linear.app/financestocks/issue/ENG-259), em novembro de 2026.
A [correção do gate](https://github.com/Vesconte-project/finance-infra/pull/190)
preserva os guards e muda o caminho; por si só não demonstra acesso na identidade
real nem a instalação concluída. São casos que motivam estas provas, não uma
suite executável incluída nesta Skill nem requisitos universais de layout.
