# Recolher metadados privilegiados sem transformar o diagnóstico em operação

Usa quando um incidente de serviço ou worker exige informação que o acesso normal de
leitura não fornece. Primeiro procura o diagnóstico no mecanismo operacional existente.
Um leitor privilegiado pontual justifica-se para uma lacuna concreta; repetir o mesmo
pedido a cada release é sinal para o integrar na observabilidade autorizada.

## Fronteiras que o leitor precisa de provar

- **Fonte executada:** se o operador adotar um pacote selado, copia o helper e as suas
  dependências para uma área protegida e compara os hashes dos bytes copiados. Num host
  Linux observado usou-se propriedade root e modo `0400`, com diretórios protegidos,
  recusa de symlinks/substituições e Python isolado. O hash identifica o código; não
  autoriza a execução, e `0400` sozinho não prova confiança nem protege os ancestrais.
- **Admissão atual:** se a leitura depende de uma manutenção terminar, verifica a prova de
  conclusão e a ausência de manutenção em curso antes de abrir a base. Um recibo antigo
  de sucesso não prova sozinho que o recurso está hoje disponível. Revalida os guards
  globais antes e depois. Um lock partilhado só coordena escritores que usam o mesmo
  lock exclusivo; não promete isolamento de comandos externos.
- **Identidade e efeitos:** obtém a ligação da configuração efetiva confirmada, apenas em
  memória, e verifica a identidade PostgreSQL efetiva. Quando a prova inclui permissões
  de ficheiros/processos, reproduz também a identidade de sistema relevante. Nunca
  troques para uma role mais poderosa para fazer o leitor passar.
- **Leitura limitada:** declara transação `READ ONLY`, timeout de statements e de locks;
  limita linhas e duração. Se precisares de snapshots coerentes, usa o isolamento
  apropriado e declara se as fases partilham a mesma transação. Um nome de função
  `inspect` não impede efeitos: exclui publicação, flows, fornecedores, alertas e
  inicializações de aplicação que possam escrever.

Num leitor que cria a sua cópia protegida ou relatórios, diz que esses ficheiros locais
são escritos. A promessa relevante é a ausência de mutações no sistema diagnosticado;
se a autorização proíbe qualquer escrita, esse desenho também precisa de mudar.

## A fronteira de apresentação é diferente da identidade interna

Projeta na query apenas metadados necessários e aplica uma allowlist à saída. Chaves de
ligação e referências podem ser comparadas em memória ou na base para devolver um booleano,
sem publicar o valor. Não devolvas objetos completos para os mascarar depois.

Valida tipos, limites e contagens sem inventar uma gramática de identificadores mais
restrita do que a do produtor. Num diagnóstico observado, um guard de ticker bloqueou
cinco fases dependentes antes da primeira análise. Alargar a expressão por tentativa
voltou a falhar: o universo continha entradas de formato inesperado. Foi necessário
preservar os identificadores no cálculo e filtrar apenas a apresentação, indicando
comprimento/categorias e quantas saídas foram ocultadas. Remover silenciosamente essas
entradas teria mudado o denominador que se tentava explicar.

## Falhas e resultados úteis

Dá nome às fases e devolve código estático, classe e SQLSTATE, sem mensagem bruta, SQL
com parâmetros ou ambiente. Depois de uma query falhar, usa uma transação/savepoint novo
antes de continuar fases independentes. Falhas de integridade, autorização ou admissão
global terminam a leitura; uma fase dependente não pode inventar inputs para passar.

Distingue `completo`, `parcial` e `não observado`. Uma fase falhada não deve esconder as
outras, nem um resumo verde pode representar fases que não correram. Conserva tentativas
anteriores. Para output grande, grava resultado sanitizado com nome único e sem seguir
symlinks/sobrescrever; mostra ao operador só estado, destino e digest. Não imponhas cópia
manual de centenas de linhas para o agente poder analisar a evidência.

## Evidência e alcance

Caso de diagnóstico de builds/registry, Linux e PostgreSQL 16, **30/10/2026**: leitores
revistos pelo operador exigiam conclusão de manutenção, usavam identidade efetiva e
transações só de leitura. As duas primeiras versões falharam no guard de identificadores;
a versão corrigida completou as sete fases, com zero mutações na base. Relatórios
sanitizados passaram a ser guardados automaticamente após um output demasiado grande
para copiar. Testes locais passaram de 14 para 22 ao cobrir os formatos e a apresentação.

Isto suporta o método e a separação entre falha da sonda e falha do serviço. Não prova
que root, esse modo de ficheiro, esse isolamento ou um recibo de manutenção sejam
necessários para toda a leitura. Não executar uma sonda privilegiada só porque esta
referência existe.
