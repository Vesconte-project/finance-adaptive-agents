---
name: credential-source-cutovers
description: Migrar ou retirar fontes de credenciais já usadas por serviços, reconciliar aliases divergentes ou preparar a rotação depois de exposição. Usa quando copiar o segredo, mudar o consumidor e revogar o acesso antigo são etapas distintas; não para criar um segredo inicial sem consumidores existentes nem para configuração sem autenticação.
---

# Mudar a fonte não prova que a credencial funciona

A decisão que esta Skill muda: **cópia fiel, uso da nova fonte, autenticação e
revogação são quatro provas diferentes**. Um ficheiro protegido e um serviço
saudável podem coexistir com uma password inválida num percurso raramente usado.
Não declares a migração ou a rotação concluída com a prova de outra etapa.
Esta Skill informa a preparação e a revisão; não concede acesso a segredos,
autorização para testar credenciais nem permissão para alterar serviços.

**Âmbito da evidência.** Incidentes repetidos num host, 14–16/10/2026, com
PostgreSQL 16 e PgBouncer 1.25.2. Num preflight, um perfil coincidia com um
password-file desatualizado; outra fonte autenticava. Noutro corte, dez aliases
de um serviço não autenticavam apesar de HTTP saudável e agendamentos pausados.
As correções foram separadas por fase. A 20/10/2026, na troca do login de um
builder e na ativação do login próprio de uma API, uma sonda de identidade
falhou só no salto pelo pool e a equivalência do builder foi provada contra uma
referência. Isto fundamenta a distinção entre provas, não um procedimento
universal para esses produtos ou versões.

## Inventaria dependências, não apenas ficheiros

Identifica a fonte proposta como canónica e os consumidores reais: ficheiros,
renderers, referências em units, wrappers, perfis de migração, pools e caminhos
de recuperação. Inclui valores por omissão operacionais que ainda apontem para
a origem antiga, mesmo quando uma variável normalmente os substitui.

Regista, sem valores, qual identidade precisa de cada credencial, onde a obtém,
por que percurso autentica e quem governa a mudança. Confirma também o que o
backup e o inventário de segredos precisam de conhecer antes do corte. Não
copies credenciais para o catálogo, comentários, argumentos ou logs para
facilitar a comparação. Uma cópia de recuperação continua a ser um segredo.

Se a informação exigir privilégio que o agente não tem, prepara uma comparação
privada para o operador, com saída limitada a metadados e veredictos. Não
alargues permissões nem uses acesso ao motor de contentores como atalho.

## Não confundas as quatro provas

1. **Cópia fiel:** o material pretendido chegou ao destino com proteção adequada.
   Comparação privada de conteúdo pode provar isto; não prova validade remota.
2. **Uso efetivo:** o consumidor obtém a credencial pelo destino novo, incluindo
   os caminhos de arranque e de execução diferida. Um ficheiro novo sem
   referências ativas não é um cutover.
3. **Autenticação e identidade:** o percurso real aceita a credencial e devolve
   a identidade esperada. Se houver pool ou proxy, discrimina os saltos que a
   decisão exige. Um endpoint HTTP genérico não prova acesso à base.
   A sonda tem de ser aceite por cada salto tal como está configurado: um
   pooler pode recusar parâmetros de arranque que a base direta aceita. No caso
   observado, PgBouncer só ignorava `extra_float_digits` e recusou
   `options=-c default_transaction_read_only=on` com "unsupported startup
   parameter", enquanto a ligação direta passava. A falha era da sonda, não da
   credencial. Usa um arranque sem parâmetros extra e só uma leitura inócua
   (por exemplo `current_user` e `session_user`); se precisares de impor
   leitura no pool, confirma primeiro a configuração efetiva do pooler. Quando
   uma sonda falha num só salto, separa as variantes por porta e parâmetro antes
   de concluir que a credencial está errada.
4. **Revogação:** depois da rotação autorizada, a credencial nova funciona e a
   antiga já não dá acesso no âmbito previsto. Apagar a cópia local não prova
   revogação no fornecedor.

Quando duas fontes divergem, não escolhas pela data, pelo nome “oficial” ou
pela igualdade com um terceiro ficheiro. Usa evidência privada de autenticação,
identidade e dependências, sob a autorização existente. Não experimentes
passwords em massa nem provoques bloqueios de conta para descobrir a certa.

## Faz o corte por fronteiras verificáveis

Prepara o destino e os consumidores antes de retirar a origem. Mantém uma
forma de recuperação protegida apenas enquanto fizer parte do plano aprovado;
um arquivo indefinido conserva a exposição. Define quem o retira, quando e
qual prova permite fazê-lo. Confirma a identidade dos ficheiros antes de uma
limpeza, para que uma troca por symlink não redirecione a eliminação.

Uma divergência descoberta durante o corte não autoriza mudar passwords ou
reativar trabalho pausado. Distingue falha introduzida pela migração de falha
preexistente. Se o operador aceitar diferir uma condição conhecida, limita-a
aos consumidores e erros exatos, com responsável e condição de saída. Conserva
o estado de aviso: isso não torna o serviço operacional nem dispensa outras
verificações. Qualquer falha fora desse âmbito continua a bloquear.

Rotação e mudança de fonte podem ter janelas diferentes. Antes de revogar,
prova os consumidores da credencial nova e os percursos de recuperação; depois,
confirma a recusa da antiga por um teste autorizado e seguro. Reinicia ou
recarrega apenas o que o mecanismo real exigir. Não repitas um comando de
rotação só porque o recibo seguinte falta: primeiro determina se já mudou a
credencial. Uma revogação externa não se desfaz restaurando um ficheiro antigo.

## Trocar o login de um serviço que produz dados

Quando o consumidor gera saídas (um build, um job de agregação), uma execução
bem-sucedida com o login novo não prova que nada se perdeu: permissões em falta
podem produzir menos resultados sem erro. Prova a equivalência com uma
**referência**:

- Corre primeiro uma execução real com o login antigo e o mesmo código, receita,
  configuração e corte de inputs, e regista o recibo dela. Não reconstruas a
  referência a partir de totais antigos.
- Corre a execução candidata com o login novo e compara por unidade de saída,
  incluindo as vazias e o motivo de estarem vazias. "7 de 8 publicadas" só é
  aceitável se a referência tiver exatamente o mesmo conjunto de vazias pelo
  mesmo motivo. No caso observado, uma combinação vazia por falta de dados de
  origem parecia uma falha de permissões até a referência mostrar o mesmo.
- Se a troca falhar antes de a candidata produzir saídas, a referência continua
  válida enquanto for a última execução. Retoma a partir dela em vez de a repetir:
  revalida que não houve execução posterior, arquiva o marcador da tentativa
  falhada sem o apagar e regista a reentrada. Qualquer execução nova, mesmo
  falhada, invalida a referência. Se um agendador puder correr entretanto,
  mantém-no parado de propósito e com prazo, ou aceita repetir a referência.

## Sinais de falha e conclusão

- Comparações iguais, mas autenticação recusada: a origem pode estar coerente
  e desatualizada. Verifica identidade, endpoint e erro de autenticação sem
  publicar a resposta sensível.
- Serviço ativo, mas nenhum percurso autenticado desde o corte: falta prova
  de uso. Exercita apenas a operação mínima autorizada ou deixa-a pendente.
- Origem antiga ainda referida por um default, renderer ou recuperação: o
  inventário está incompleto; não a elimines por parecer duplicada.
- Avisos conhecidos transformados em sucesso geral: perdeu-se a fronteira
  entre retirada de fontes, reparação de consumidores e rotação.
- Contagem de verificações diferente da esperada: deriva o número esperado dos
  consumidores configurados no momento, não de uma constante. Um consumidor
  novo legítimo (por exemplo, um login próprio criado no mesmo dia) muda a
  contagem; um consumidor desconhecido também. Compara o conjunto exato.

O recibo final distingue essas etapas, com evidência posterior à mudança,
metadados dos destinos, consumidores verificados e pendências explícitas.
Não contém passwords, verificadores, URLs privadas nem dumps de ambiente.

## Quando não aplicar

Uma credencial inicial sem aliases ou consumidores anteriores não precisa de
um cutover. Configuração sem autenticação pertence ao rastreio de configuração.
Nesse caso, identifica o consumidor, as fontes aplicáveis, a precedência e o
valor efetivamente consumido, sem concluir que um ficheiro instalado já foi
carregado. Mover dados persistentes é outra operação: exige um plano específico
de consistência, coordenação dos escritores, cutover e recuperação das escritas
posteriores. As quatro provas desta Skill não completam essa migração. Não
substituas os mecanismos de rotação e recuperação mantidos pelo projeto por uma
receita genérica.
