# A validação também pode alterar o que valida

**Decisão:** verifica o selo depois da última validação, não apenas os hashes
antes dela. Uma operação Git apresentada como leitura pode atualizar metadados,
como o índice. Conteúdo correto não prova que a árvore continua só de leitura.

**Evidência:** caso único num host Linux, 13/10/2026. A release passou a
validação de commits e conteúdo, mas a prova final dos metadados recusou;
oito índices precisaram de ser novamente selados. Versão Git não registada.
Não se conclui que todo comando Git escreva, nem que qualquer versão o faça
nas mesmas condições.

## Preserva a cadeia de confiança durante a validação

Quando Git faz parte da release, o seu controlo inclui mais do que os blobs:
configuração local, hooks, fsmonitor, caminhos alternativos de objetos e opções
de ambiente podem influenciar os comandos. Um SHA certo não torna confiável a
configuração herdada de outra identidade. Prepara a cópia segundo a fronteira
de confiança aprovada; não executes como root numa árvore mutável de outro
utilizador para “validá-la primeiro”.

Finaliza os passos que escrevem antes do selo. Para comandos posteriores,
usa modos que não escrevam quando existirem e forem adequados; confirma a
semântica na versão instalada. Não relaxes permanentemente as permissões do
índice para fazer passar uma verificação.

## Sinais e prova final

Um sinal característico é a combinação “SHA e hashes iguais” com “metadata
seal falhou”. Identifica qual passo alterou proprietário, modos ou conteúdo;
não atribuas automaticamente o problema ao Git. Compara antes/depois numa
preparação descartável ou noutra prova autorizada.

Depois da última operação de validação, volta a exigir os proprietários e modos
do contrato, destinos seguros de symlinks e integridade do conteúdo. Confirma
que a própria verificação final não volta a criar a divergência. Regista o
estado como selado apenas após essa prova.

**Não aplicar:** artefactos sem Git ou instalações cujo contrato separa
explicitamente metadados mutáveis do código protegido; nesses casos valida
essa separação, sem impor que toda a árvore seja só de leitura.
