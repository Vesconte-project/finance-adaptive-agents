---
name: failure-mode-self-review
description: Rever o próprio desenho ou PR antes de o entregar, quando o código vai correr sozinho em produção (serviços, timers, pipelines, gates, instaladores, filtros de seleção, alertas). Faz as perguntas de modos de falha que um revisor faria, em vez de só confirmar que o caminho feliz e os testes passam. Não para alterações puramente cosméticas ou código sem efeito operacional.
---

# Autorrevisão por modos de falha

Testes verdes provam que o código faz o que o autor imaginou. Um revisor pergunta o que
acontece no caso que o autor não imaginou. Esta skill serve para fazer essas perguntas
**antes** de entregar, para que o revisor encontre menos e a produção não encontre nada.

**Evidência.** Uma semana de operação de uma plataforma num único host (2026-10). Cada
pergunta abaixo teria apanhado, na autorrevisão, um defeito que só foi encontrado na revisão,
na instalação ou já em produção. Os casos estão em
[references/casos-2026-10.md](references/casos-2026-10.md).

## Quando usar

Antes de abrir ou atualizar um PR (ou entregar um bloco) cujo código corre sem uma pessoa a
ver: workers, timers, flows agendados, gates de release, instaladores, filtros que decidem o
que é processado, emissores de alertas ou de estado. Faz a revisão com o diff à frente e
responde a cada pergunta por escrito, nem que seja "não se aplica, porque…".

## As perguntas

**1. Uma falha parcial bloqueia o todo?**
Procura acoplamentos de N para 1: um ciclo que processa N itens e falha inteiro por causa de um,
um `OnSuccess=`/`&&` entre passos, um lote cuja falha descarta os itens bons, um orçamento
alimentado por um sinal ruidoso. Pergunta: "se um item estiver estragado para sempre, os outros
continuam a funcionar e o problema fica visível?"

**2. Quanto custa quando não há nada para fazer?**
Um timer de minuto a minuto multiplica tudo por 1 440 por dia: tokens pedidos, assinaturas,
chamadas a APIs externas, leituras de tabelas inteiras, escritas de estado e linhas de log.
O estado estacionário deve custar quase zero. Faz o trabalho caro só quando algo mudou.

**3. A verificação prova o efeito ou só a existência?**
"O timer está ativo", "o serviço está active", "o ficheiro foi escrito" e "o workflow ficou
verde" provam presença, não resultado. Verifica o efeito real de ponta a ponta: um ciclo que
entregou, uma porta que responde, uma linha que chegou ao destino. Distingue "aceite" de
"concluído" sempre que houver espera ou adiamento.

**4. O que acontece com dados que o teste não tem?**
Corre a lógica nova de seleção, exclusão ou classificação contra o estado real (só em leitura e
com autorização) e compara com a instalada: quem entra, quem sai, quem fica bloqueado. Uma
regra que parece estrita nos sintéticos pode excluir casos reais que hoje funcionam.

**5. O que é diferente no host alvo?**
Lista as suposições sobre o ambiente (tipo de filesystem, versões, units template, permissões,
fusos, limites de memória) e confirma-as no alvo antes de instalar. Corre no `plan` as mesmas
verificações de admissão que vão correr depois do `apply`.

**6. Um evento atrasado ou repetido pode estragar o estado atual?**
Retries, entregas duplicadas, respostas perdidas, ordem trocada e pedidos substituídos. Um
evento velho nunca pode sobrepor um mais novo. A operação deve ser idempotente ou detetar o
duplicado. Um sucesso depois de uma falha não deve deixar sinais contraditórios por explicar.

**7. Quando falha, alguém fica a saber e consegue agir?**
Cada estado alcançável (aceite, adiado, concluído, falhado, revertido, expirado) tem de ter um
destino que alguém lê. As recusas imprimem um código fixo e a fase, não só o nome da exceção.
Uma exclusão silenciosa é pior do que uma falha ruidosa.

**8. A ausência de dado está a fabricar um dado?**
Um timestamp em falta passa a "agora"? Uma resposta vazia passa a "sem retenção"? Uma
re-obtenção curta passa a "atrasado" quando o dado já estava validado? Um valor em falta deve
ficar em falta e ser classificado, nunca preenchido com um valor plausível.

**9. Como se desfaz, e o desfazer foi testado?**
Rollback automático verificado (hashes, modos, estado), um diretório de estado novo por
tentativa, e remoções que voltam a verificar as proteções no momento de apagar, de preferência
com quarentena. O que não tem rollback é declarado como tal.

**10. Que passos humanos ficam por fazer, e estão escritos?**
Credenciais a criar, permissões mínimas, onde guardar segredos sem chat nem argv, decisões que
só o dono pode tomar. Entrega as instruções junto com o PR, não depois de alguém perguntar.

## Como entregar o resultado

No corpo do PR ou do handoff, acrescenta uma secção curta "Modos de falha considerados", com
uma linha por pergunta relevante: o risco, o que fizeste e como está provado (o teste, a prova
contra o host ou o dryrun). Marca o que fica por provar e quem o prova. Isto não substitui a
revisão independente. Serve para o revisor discutir o que é difícil, não o que era previsível.

Para um exemplo completo da secção e de como chegar a ela, lê
[references/exemplo-seccao-pr.md](references/exemplo-seccao-pr.md).

## Sinais de que a autorrevisão foi superficial

- Todas as respostas são "os testes passam".
- A verificação pós-instalação só confirma que algo está "ativo".
- Nenhuma pergunta mencionou o estado real de produção nem o host alvo.
- O PR não diz o que o humano tem de fazer a seguir.

## Quando não aplicar

Alterações sem efeito operacional (documentação, renomeações internas sem mudança de
comportamento, testes puros). Em scripts de uso único corridos por uma pessoa a ver, as
perguntas 2 e 6 pesam menos, mas a 3, a 7 e a 9 continuam a valer.
