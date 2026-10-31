---
name: incident-latent-condition-and-trigger
description: Diagnosticar um incidente ou uma regressão de dados em que algo deixou de funcionar numa data concreta sem erro óbvio, como entidades a desaparecer, contagens que caem, retenções em massa, falhas noturnas ou OOM. Usa para datar o início, cruzá-lo com as mudanças, separar a condição latente do gatilho e corrigir a causa em vez do sintoma.
---

# Condição latente e gatilho

Os incidentes mais caros raramente são "um bug novo". Quase sempre há uma **condição latente**
que existe há semanas ou meses sem efeito (dados estranhos, um limite que só aperta com volume,
uma suposição sobre o ambiente) e um **gatilho** recente que a ativa (um merge, um filtro novo,
o crescimento dos dados, outra hora de execução). Corrigir só o gatilho deixa a condição pronta
para o próximo; corrigir só o sintoma esconde as duas.

**Evidência.** Incidentes numa plataforma de dados de mercado, 2026-10:
- 58 entidades sem dados desde uma data concreta. A condição latente eram linhas de registo de
  julho que ganhavam por microssegundos; o gatilho foi um merge que passou a excluir linhas
  rejeitadas. A pergunta "o que entrou nessa data?" encontrou o merge no histórico do Git.
- Um builder noturno começou a ser morto por OOM. A condição latente era carregar tabelas
  inteiras; o gatilho foi o histórico crescer até ao limite do cgroup, sem nenhuma alteração de
  código.
- Centenas de retenções numa run à meia-noite. A condição latente era confiar numa re-obtenção
  do fornecedor; o gatilho era a hora da run, em que o fornecedor ainda não devolve o dia.

## Método

1. **Data o início com precisão.** Encontra o último momento bom e o primeiro mau (a última data
   com dados, o primeiro run falhado, o dia em que a contagem caiu). Sem uma data, não há
   cruzamento possível.
2. **Lista o que mudou nessa janela.** Merges e deploys (histórico do Git e recibos de release),
   mudanças de configuração, dados novos ou migrados, volume, versões de dependências e horários.
   Pergunta explicitamente: "o que entrou entre o último dia bom e o primeiro mau?"
3. **Mede o alcance.** Quantas entidades, regiões e runs. Quem está afetado e quem não está? O
   conjunto afetado tem uma característica comum (linhas duplicadas, uma bolsa, um tamanho, uma
   hora)? Uma coincidência exata entre dois conjuntos ("as 52 sem evento são exatamente as 52
   com linhas duplicadas") é forte evidência.
4. **Sobe uma escada de evidência só de leitura.** Primeiro as contagens, depois 2–3 amostras e
   depois a origem (quem escreveu, quando, com que código). Cada degrau responde a uma pergunta
   do anterior. Pede apenas os campos necessários e sem valores confidenciais.
5. **Separa a condição latente do gatilho e explica porque é que antes não falhava.** Se não
   consegues explicar porque é que funcionou até àquela data, a causa ainda não está encontrada.
6. **Corrige a causa, depois considera o sintoma.** A correção principal deve tornar a condição
   inofensiva (resolução correta, streaming, confiar no dado validado). O gatilho pode continuar.
   A limpeza de dados e as recuperações são operações à parte e revistas. Acrescenta
   visibilidade, para que a próxima ocorrência não seja silenciosa.
7. **Prova com o caso real.** A correção deve demonstrar, contra os dados ou o cenário real (em
   leitura ou em dryrun), que os afetados recuperam e que nenhum outro é afetado.

Para um exemplo completo passo a passo, um modelo de nota de investigação e as perguntas que
desbloqueiam uma investigação parada, lê
[references/exemplo-e-modelo.md](references/exemplo-e-modelo.md).

## O que não fazer

- Baixar um limiar, acrescentar tolerância, corrigir um fuso ou apagar linhas sem saber que
  transformação gerou o sintoma.
- Declarar a causa com base numa hipótese plausível sem ter explicado o "porquê agora".
- Pedir mais leituras sem dizer que pergunta cada uma responde.
- Fazer uma recuperação dos dados em falta antes de a causa estar corrigida e instalada.

## Sinais de que a investigação está presa

- Várias rondas de "hipótese não provada" sem nenhuma data de início cruzada com mudanças.
- O conjunto afetado nunca foi comparado com o não afetado.
- A correção proposta funcionaria igualmente bem se a causa fosse outra.
