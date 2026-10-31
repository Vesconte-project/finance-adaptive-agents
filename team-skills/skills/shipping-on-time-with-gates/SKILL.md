---
name: shipping-on-time-with-gates
description: Planear e executar trabalho com prazos reais (antes da próxima run, até ao fim do dia, antes de uma janela fechar), sem adiar por defeito e sem cortar salvaguardas. Usa quando há uma meta temporal, quando um merge ou instalação depende de calendários, janelas ou gates, ou quando a tentação é "fica para amanhã".
---

# Entregar a tempo sem cortar nas salvaguardas

Qualidade e velocidade não são opostas quando o trabalho é planeado a partir do prazo. O erro
comum de um agente cuidadoso é **adiar por defeito**: um input em falta, uma revisão pendente ou
uma janela apertada viram "amanhã", e amanhã aparece outro motivo. O erro oposto é cortar uma
salvaguarda para cumprir a hora. O objetivo é cumprir a meta mantendo os gates: prova, revisão,
rollback e janelas.

**Evidência.** Um dia de operação com o dono a pedir "não vamos adiar" (2026-10-30):
- uma instalação bloqueada por 4 inputs obrigatórios inexistentes foi feita no mesmo dia, com
  os inputs derivados de medições reais do host e rotulados como derivados;
- dois defeitos que só existiam no host foram apanhados pela verificação do próprio instalador,
  revertidos sozinhos, corrigidos num PR revisto e instalados cerca de uma hora depois;
- um merge que, feito às 19:42, ficaria adiado até à manhã seguinte (havia uma run às 20:00 e o
  gate exige 45 minutos livres) foi feito às 20:50 e ficou instalado e verificado antes da run
  das 22:30;
- leitores e dryruns para o dia seguinte foram preparados e revistos na véspera, prontos a correr
  logo de manhã.

## Método

1. **Escreve a meta com hora e o porquê.** Por exemplo: "instalado antes da run US das 22:30,
   para as empresas recuperarem esta noite". Uma meta sem hora não orienta decisões.
2. **Planeia de trás para a frente.** A partir da meta, subtrai o caminho até ao efeito: a
   primeira run que usa a mudança, o gate (janelas, margem antes de runs, supervisão), o deploy,
   o CI e a revisão. O resultado é a hora-limite de cada passo (por exemplo, "merge até às
   21:15"). Lê o calendário real de runs e as janelas; não as adivinhes.
3. **Encontra o caminho crítico e paraleliza o resto.** Enquanto o código está a ser escrito,
   prepara a prova (o leitor, o dryrun, a medição), a mensagem para o próximo agente e as
   instruções para o humano. Nada que possa correr em paralelo deve esperar em série.
4. **Quando falta um input, procura uma forma legítima de o obter hoje.** Muitas vezes pode ser
   derivado de observações reais (e rotulado como derivado), substituído por uma versão mais
   pequena da mudança ou provado em leitura. Nunca inventes valores para passar um gate. Se não
   houver forma legítima, diz exatamente o que falta e quem o desbloqueia.
5. **Entrega a fatia mais pequena que produz o efeito.** Separa o que é preciso para a meta do
   que é melhoria. A melhoria entra a seguir, com o seu próprio prazo, e não fica esquecida.
6. **Mantém os gates e torna-os rápidos.** Revisão com um veredito claro, prova fixada ao SHA,
   rollback automático e janelas respeitadas. O que acelera é preparar tudo para que o gate
   passe à primeira, não saltá-lo.
7. **Quando algo falha perto do prazo, decide depressa.** Reverte (o rollback automático já
   devia existir), corrige a causa se couber no tempo e volta a tentar. Se não couber, declara a
   nova hora-limite (por exemplo, "amanhã, entre as 08:30 e as 11:00, preparado de véspera") e o
   que fica pronto entretanto.
8. **Diz a hora em cada mensagem que depende dela.** Por exemplo: "faz merge entre as 20:15 e as
   21:15 UTC", "corre antes das 17:35". O dono não deve ter de calcular janelas.

Para exemplos com horas reais (uma correção antes de uma run noturna, uma instalação com inputs
em falta, a preparação de véspera) e um modelo de planeamento, lê
[references/exemplos-e-modelo.md](references/exemplos-e-modelo.md).

## O que não é aceitável

- "Fica para amanhã" sem a hora nova, o motivo concreto e o que fica preparado hoje.
- Cortar uma prova, uma revisão ou um rollback para caber no prazo.
- Esperar por um passo que podia correr em paralelo.
- Propor um merge sem verificar o calendário de runs e as janelas do gate.

## Quando não aplicar

Trabalho exploratório sem meta temporal, ou mudanças que, por decisão do dono, só entram numa
janela de manutenção marcada. Mesmo aí, prepara tudo antes da janela.
