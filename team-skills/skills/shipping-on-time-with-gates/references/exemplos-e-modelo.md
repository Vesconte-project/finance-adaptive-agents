# Exemplos e modelo de planeamento de trás para a frente

## Exemplo 1: correção que tem de chegar antes de uma run noturna

Meta: "as 49 empresas recuperam na run US das 22:30 UTC".

| Passo (de trás para a frente) | Duração/regra | Hora-limite |
|---|---|---|
| Primeira run que usa a correção | Run US agendada | 22:30 |
| Gate do deploy | Não instala com uma run a menos de 45 min, nem numa janela proibida | O deploy tem de começar até às 21:45 |
| Deploy (build, ativação, verificação) | Até 30 min | — |
| CI no main depois do merge | ~10–15 min | Merge até às ~21:15 |
| Run das 20:00 a decorrer | O gate adia qualquer pedido feito antes das ~20:10 | Merge a partir das ~20:15 |
| Dryrun com dados reais do head final | ~20 min, em paralelo com o CI do PR | Até às ~20:00 |
| Revisão do head final | — | Até às ~19:30 |

Resultado: merge às 20:50, deploy verificado, empresas recuperadas na run das 22:30. Um merge às
19:42 teria ficado adiado até à manhã seguinte.

## Exemplo 2: instalação bloqueada por inputs inexistentes

O instalador exigia 4 inputs que o host ainda não tinha (orçamentos de espaço por componente,
registo de referências, ledger de intenções e baseline de alertas). Em vez de "fica para outro
dia":
- os orçamentos foram derivados de medições reais (2× a maior release guardada, medida na hora)
  e rotulados como derivados;
- o ledger ficou vazio só depois de confirmar na API que não havia intenções a adotar;
- o registo e a baseline foram gerados a partir de documentos e recibos atuais;
- o `plan` correu a mesma admissão do `apply` e apanhou dois defeitos do host, que foram
  corrigidos num PR revisto. A instalação passou à segunda tentativa, no mesmo dia.

## Exemplo 3: o que fica preparado quando o prazo é amanhã

Quando um passo só pode correr amanhã (fim de semana, outra janela), deixa hoje: o leitor ou o
dryrun selado e revisto, com o SHA256 e a janela recomendada; a mensagem para o próximo agente;
os critérios de aprovação; e a lista do dia com as horas. Amanhã o trabalho começa às 08:30 com
a execução, não com a preparação.

## Modelo

```markdown
**Meta:** <efeito> até <hh:mm UTC> porque <razão>.
**Caminho até ao efeito (de trás para a frente):**
- <primeira run/uso> — <hh:mm>
- <gate/janela> — regra — <hh:mm limite>
- <deploy> — duração — <hh:mm>
- <CI> — duração — merge até <hh:mm>
- <revisão/prova> — até <hh:mm>
**Em paralelo agora:** <provas, mensagens, instruções ao humano>
**Inputs em falta e como os obter hoje:** <derivado de… / versão menor / prova em leitura>
**Fatia mínima:** <o que entra> | **Depois:** <melhorias, com prazo>
**Se falhar:** <rollback automático> → <nova tentativa até hh:mm> → <senão: nova hora e o que fica pronto>
```
