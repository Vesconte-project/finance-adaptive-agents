---
name: availability-holds-from-provider-signals
description: Rever ou corrigir retenções derivadas de respostas de um fornecedor externo (preço diário, cotação, histórico) num pipeline com orçamento agregado de retenções. Usa quando muitas entidades ficam retidas de repente, quando o orçamento falha apesar de existirem dados válidos, ao acrescentar um sinal ao gate ou quando sessões em falta deixam de ser revisitadas após recuperação parcial abaixo da tolerância agregada.
---

# Retenções a partir de sinais do fornecedor

Um pipeline pode reter uma entidade quando a resposta do fornecedor parece atrasada,
incompleta ou falhada. Um orçamento agregado protege a publicação contra falhas extensas;
sinais mal classificados podem fazê-lo falhar mesmo quando os dados necessários estão
válidos. No sentido inverso, voltar à tolerância agregada pode ocultar faltas residuais.

Este Skill informa o trabalho; não autoriza alterações, exceções, reparações ou operações
em produção. Preserva o contrato de publicação, o universo selecionado e as janelas já
autorizadas.

## Evidência de origem

O relato operacional fornecido descreve um pipeline de mercado:

- Numa região com 83 entidades, 74 ficaram retidas; 64 tinham apenas cotação atrasada,
  apesar de o preço diário da sessão estar fresco, e a região falhou inteira.
- Uma execução agregada marcou 510 entidades como preço atrasado porque a resposta
  reobtida terminava na véspera após normalização. A linha da sessão esperada tinha sido
  publicada e validada cerca de 90 minutos antes.

Estes são relatos do operador, não resultados reproduzidos por este pacote. Sustentam
investigar a classificação dos sinais e a validade dos dados existentes; não estabelecem
que preço diário substitui cotação em qualquer produto.

A referência [Recuperação de sessões residuais](references/residual-session-recovery.md)
regista um caso sintético reportado: restaurar um lote resolveu 100 de 102 faltas, mas as
duas restantes precisavam de continuar a ser observadas mesmo abaixo da tolerância agregada.

## Regras de decisão

1. **Classifica cada sinal pelo contrato de publicação.** Identifica quais os inputs,
   prazos e condições de validade exigidos pelo consumidor. Uma cotação atrasada pode ser
   apenas um aviso quando esse contrato exige somente o preço diário e este satisfaz os
   requisitos atuais. Se a cotação também for obrigatória, o preço diário não elimina a
   retenção. Não reclassifiques um sinal apenas para passar o orçamento.
2. **Verifica unidades e semântica temporal por campo.** Antes de converter um timestamp,
   confirma a unidade documentada pelo fornecedor para esse campo, incluindo campos epoch;
   não pressuponhas segundos ou nanossegundos. Confirma também o fuso e a convenção de
   sessão. Se o contrato usa sessões de bolsa, resolve a sessão segundo o calendário e
   fuso aplicáveis, em vez de comparar diretamente datas UTC. Noutros domínios, usa a
   referência temporal do respetivo contrato. Um timestamp ausente permanece ausente:
   substituí-lo por agora fabrica frescura.
3. **Avalia o dado canónico antes de reagir a uma reobtenção pior.** Se a resposta termina
   antes da sessão esperada, verifica a chave exata no armazenamento canónico e se a linha
   ainda satisfaz os requisitos atuais de validade, proveniência, ajustes e frescura.
   Só quando o contrato permite reutilizá-la pode a regressão do fornecedor ser tratada
   como aviso, sem retenção por essa causa. Não sobrescrevas dados válidos com uma resposta
   pior. A mera presença de uma linha ou de cache não limpa uma retenção com causa própria.
4. **Preserva observações anteriores ao descarte.** Quando a normalização remove linhas,
   regista por entidade a última data bruta observável, o fuso e as contagens de descartes
   por motivo, sem valores de negócio. Mantém ausente o que não foi observado. Sem esse
   diagnóstico, uma resposta sem o dia esperado pode ser confundida com uma resposta que
   o continha mas tinha campos inválidos. Descartar a linha não demonstra que a causa de
   rejeição desapareceu.
5. **Investiga causas antes de alterar o orçamento.** Separa retenções por motivo e confirma,
   numa amostra, a existência e a validade dos dados canónicos. Identifica a transformação
   ou condição que gerou o sinal antes de propor outro limiar ou tolerância.
6. **Preserva a falha do orçamento no fluxo agregado.** Se o fluxo captura essa falha para
   continuar outras fases, garante que emite o alerta e termina com falha mesmo se uma
   fase posterior também falhar. Conserva os diagnósticos de ambas as causas.
7. **Separa deduplicação, cobertura, exceção e recuperação.** Um alerta deduplicado, uma
   exceção aplicável ou o agregado dentro da tolerância não demonstram chegada dos inputs.
   Mantém observáveis as sessões pendentes das entidades selecionadas dentro da janela
   já autorizada. Ao alterar o planeador, o ledger ou o fecho de incidentes, lê a
   [referência de recuperação](references/residual-session-recovery.md).

## Diagnóstico rápido

1. Separa retenções por motivo e por execução, incluindo âmbito e hora.
2. Para algumas entidades afetadas, verifica em leitura e com acesso autorizado a chave
   canónica exata: quem a escreveu, quando e se satisfaz o contrato atual. Compara o
   diagnóstico bruto com o normalizado. Sem esse acesso, usa evidência sanitizada
   disponível e declara a verificação por provar.
3. Compara as janelas pedidas, incluindo limites exclusivos do fornecedor, entre a
   execução que funcionou e a que reteve.
4. Distingue sinal mal classificado, conversão temporal incorreta, regressão do fornecedor
   e retenção sustentada por dados ausentes ou inválidos.
5. Após recuperação parcial, cruza as sessões ainda pendentes com as efetivamente
   avaliadas pela próxima execução. Uma janela que começa depois delas deixa de observar
   a falta; não demonstra recuperação.
6. Verifica a correção no percurso real entre resposta, normalização, diagnóstico e decisão
   do gate. Fixtures construídas apenas após a transformação não provam que a informação
   relevante chegou ao consumidor.

## Limites

Não uses este Skill apenas porque uma tarefa envolve datas de mercado. O seu contexto é
retenção derivada de sinais de fornecedor com orçamento agregado; não substitui o contrato
de fontes internas, um guia de calendários ou uma política geral de incidentes.

A referência trata faltas de inputs identificadas por sessão. Não define recuperação de
inputs inválidos, backfills de ajustes, limiares universais ou durações de aprovação. Uma
nova observação validada pode alterar a decisão; uma mudança de seleção, silêncio do alerta
ou descarte na normalização não a substitui.
