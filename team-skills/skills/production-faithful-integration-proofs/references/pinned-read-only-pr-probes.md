# Provar o impacto de um PR no alvo autorizado, sem o instalar

Usa quando testes sintéticos passaram mas a decisão depende de permissões ou combinações
que os dados existentes podem conter. A prova complementa testes descartáveis; não deve
contactar o fornecedor nem executar mutações para simular o resultado que se deseja.

Executa a sonda apenas se a autorização existente abranger esse alvo, a identidade efetiva
e a execução desse código em leitura. A Skill não concede esse acesso. Sem esse âmbito,
usa evidência sanitizada disponível e declara as permissões e combinações por verificar.

## Fixar o código que realmente está a ser provado

1. Fixa o head revisto e a baseline instalada, com todas as dependências necessárias;
   confirma os bytes obtidos contra essas revisões. Um branch móvel ou a cópia importada
   do venv não identifica o código novo. Numa repetição para outro head, preserva a prova
   anterior e mostra o diff do leitor, dos pins e das fontes.
2. Usa a função do PR e o seu **SELECT literal**, com a identidade efetiva do consumidor.
   Reimplementar a regra ou projetar menos colunas pode esconder precisamente a falha
   de permissões que a nova versão teria. Projeta o segredo/referência em booleanos no
   próprio SQL quando esse é o contrato real; não o exponhas no resultado.
3. Uma opção relatada foi extrair o corpo do loader por AST, sem o alterar, e adaptar
   apenas a função de acesso à base para uma transação `READ ONLY` já aberta. O adaptador
   recusava queries/argumentos diferentes do SELECT fixado. O resolver e as dependências
   puras vieram do mesmo commit e correram com a identidade do worker.

Extração por AST não é sandbox nem prova automática de equivalência. Confirma os globals,
decorators, imports, closures e estado de módulo de que a função depende. Se alterares a
inicialização ou uma dependência necessária, limita a conclusão ou usa outra prova
controlada. Um read-only da base não impede HTTP, escrita de ficheiros ou criação de jobs;
revê os caminhos alcançáveis antes da execução para excluir esses efeitos. Quando viável,
isola o processo, restringindo escritas e ligações ao necessário para a leitura autorizada
da base. Não executes código hostil ou de efeitos incertos apenas por estar numa transação
READ ONLY. O URI fica apenas em memória e não deve aparecer nos relatórios.

## Comparar o pipeline de seleção, não só o loader

Reconstrói as mesmas etapas antes/depois: universo inicial, normalização, resolução,
filtro de exclusão e denominador do gate. Por partição, mostra entradas, saídas,
bloqueados, decisões e avisos. Distingue um bloqueado que sai do refresh mas volta ao
orçamento de retenções. Deduplica a união de motivos; duas causas para a mesma entidade
não são duas entidades.

Confronta os **conjuntos exatos** esperados, não apenas as cardinalidades. Uma saída não
prevista precisa de atribuição, mesmo se o total final parecer correto. Avisos agregados
não demonstram, sem correspondência, qual entidade recebeu cada aviso. Se o formato do
leitor só apresenta contagens, conserva essa limitação em vez de afirmar uma prova
individual inexistente.

Se a baseline escolhe a última linha por timestamp e há empate no máximo, reporta a
indeterminação do seu SELECT/ordenação. Acrescentar um desempate à sonda sem o implementar
na baseline mudaria o comportamento que se pretende medir.

## O limite da conclusão

- Acesso às novas colunas prova a permissão daquele SELECT, não permissões de escrita.
- Um diff de seleção prova a resolução daquele snapshot. Não reconstrói automaticamente
  o registry de uma run antiga a partir do estado atual e de `updated_at`.
- Contar checkpoints atuais num gate é uma simulação estática. Uma run posterior ainda
  pode atualizar, limpar ou criar retenções; o resultado não prevê a resposta futura
  do fornecedor nem a prontidão do deploy.
- Usa códigos de erro por fase e preserva o relatório completo sanitizado apenas num
  destino apropriado e autorizado. Não devolvas chaves internas, referências, notas
  livres ou valores de negócio; o relatório técnico também não concede autorização
  de merge ou de instalação.

## Evidência e alcance

Num caso fornecido sobre um PR num repositório de ingestão de dados, uma primeira prova
do head encontrou saídas não desejadas. A repetição no head revisto preservou o mesmo
universo de entrada e deixou de produzir essas saídas ou bloqueados. As entidades afetadas
mantiveram-se incluídas, mas os conflitos só estavam apresentados em agregado. Segundo o
relato, as provas executaram os SELECTs fixados e confirmaram a identidade e o modo de
leitura; não fizeram pedidos ao fornecedor. Este pacote não inclui uma reprodução
independentemente executável dessas sondas.

Na mesma investigação, uma execução regional registara menos retenções do que o agregado
observado posteriormente. Transportar os checkpoints desse agregado para um dryrun não
provava que a próxima execução teria o mesmo número de falhas. Este caso sustenta as
fronteiras de atribuição entre snapshot, execução histórica e previsão; não estabelece
uma política universal de seleção ou de tolerância a dados.
