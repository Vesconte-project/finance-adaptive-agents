---
name: failure-mode-self-review
description: Rever o próprio desenho ou PR antes de o entregar, quando o código vai correr sozinho em produção (serviços, timers, pipelines, gates, instaladores, filtros de seleção, alertas). Faz as perguntas de modos de falha que um revisor faria, em vez de só confirmar que o caminho feliz e os testes passam. Não para alterações puramente cosméticas ou código sem efeito operacional.
---

# Autorrevisão por modos de falha

Testes verdes provam comportamentos nos casos exercitados. Um revisor pergunta o que
acontece no caso que o autor não imaginou. Esta skill serve para fazer essas perguntas
**antes** de entregar e reduzir os defeitos que chegam à revisão e à produção.

**Evidência e limites.** A orientação inicial deriva de relatos de uma semana de operação
numa plataforma com um único host. Os casos anonimizados estão em
[references/casos-2026-10.md](references/casos-2026-10.md); não constituem garantia para outros
ambientes. Um caso sintético posterior mostrou que conhecer estas perguntas não basta:
testes isolados passaram, mas uma transformação apagou evidência negativa antes da decisão
de outro componente. O método e os limites dessa prova relatada estão em
[references/mapa-de-fronteiras.md](references/mapa-de-fronteiras.md).

## Quando usar

Antes de abrir ou atualizar um PR (ou entregar um bloco) cujo código corre sem uma pessoa a
ver: workers, timers, flows agendados, gates de release, instaladores, filtros que decidem o
que é processado, emissores de alertas ou de estado. Faz a revisão com o diff à frente e
responde a cada pergunta por escrito, nem que seja "não se aplica, porque…".

Esta skill orienta a revisão; não autoriza acesso, alterações, instalação ou operações em
produção. Usa apenas o acesso e as operações já autorizados para a tarefa.

## As perguntas

**1. Uma falha parcial bloqueia o todo?**
Procura acoplamentos de N para 1: um ciclo que processa N itens e falha inteiro por causa de um,
um `OnSuccess=`/`&&` entre passos, um lote cuja falha descarta os itens bons, um orçamento
alimentado por um sinal ruidoso. Pergunta: "se um item estiver estragado para sempre, os outros
continuam a funcionar e o problema fica visível?"

**2. Quanto custa quando não há nada para fazer?**
Um timer de minuto a minuto multiplica tudo por 1 440 por dia: tokens pedidos, assinaturas,
chamadas a APIs externas, leituras de tabelas inteiras, escritas de estado e linhas de log.
Procura reduzir o custo estacionário e fazer trabalho caro apenas quando necessário,
preservando a reconciliação que o contrato exigir.

**3. A verificação prova o efeito ou só a existência?**
"O timer está ativo", "o serviço está active", "o ficheiro foi escrito" e "o workflow ficou
verde" provam presença, não resultado. Verifica o efeito real de ponta a ponta dentro do
âmbito autorizado: um ciclo que entregou, uma porta que responde, uma linha que chegou ao
destino. Distingue "aceite" de "concluído" sempre que houver espera ou adiamento.

Se a decisão depende de dados que passam entre componentes, lê
[references/mapa-de-fronteiras.md](references/mapa-de-fronteiras.md): escreve o percurso
observação → transformação → evidência → consumidor, segue um caso adversarial pelo produtor
e consumidor reais e identifica onde a prova termina. Testes separados de cada etapa não
provam a ligação entre elas.

**4. O que acontece com dados que o teste não tem?**
Quando houver acesso autorizado, corre a lógica nova de seleção, exclusão ou classificação
contra o estado real, só em leitura, e compara com a instalada: quem entra, quem sai, quem
fica bloqueado. Uma regra que parece estrita nos sintéticos pode excluir casos reais que
hoje funcionam. Sem esse acesso, usa evidência sanitizada disponível e declara a comparação
real por provar; não infiras os resultados.

**5. O que é diferente no host alvo?**
Lista as suposições relevantes sobre o ambiente: tipo de filesystem, versões, units template,
permissões, fusos ou limites de memória. Se a alteração depender de um alvo identificado,
confirma essas suposições antes de instalar, apenas com acesso já autorizado e verificações
só de leitura. Sem esse acesso ou evidência suficiente, declara-as por provar e indica quem
as poderá verificar e em que condição autorizada.

Se o processo tiver fases separadas, como `plan` e `apply`, verifica na fase prévia as mesmas
condições de admissão que serão exigidas na fase final, quando possam ser avaliadas sem
mutação. Condições mutáveis devem voltar a ser verificadas no momento da ação; um plano
válido não prova que o estado permaneceu igual.

**6. Um evento atrasado ou repetido pode estragar o estado atual?**
Retries, entregas duplicadas, respostas perdidas, ordem trocada e pedidos substituídos.
Identifica o que o contrato usa como ordem ou versão autoritativa; a ordem dos timestamps,
por si só, pode não decidir qual estado prevalece. Define e testa o comportamento esperado
para eventos atrasados e repetidos, incluindo como distinguir uma repetição da mesma operação
de operações distintas autorizadas. Usa idempotência ou deteção de duplicados quando o
contrato exigir evitar efeitos repetidos; se admitir outros efeitos, verifica-os explicitamente.
Evidência antiga ou revogada não deve apagar estado atual validado sem fundamento explícito
no contrato. Um sucesso depois de uma falha não deve deixar sinais contraditórios por explicar.

**7. Quando falha, alguém fica a saber e consegue agir?**
Cada estado alcançável (aceite, adiado, concluído, falhado, revertido, expirado) tem de ter um
destino que alguém lê. As recusas imprimem um código fixo e a fase, não só o nome da exceção.
Uma exclusão silenciosa é pior do que uma falha ruidosa.

**8. A ausência de dado está a fabricar um dado?**
Um timestamp em falta passa a "agora"? Uma resposta vazia passa a "sem retenção"? Uma
re-obtenção curta passa a "atrasado" quando o dado já estava validado? Quando a ausência
representa desconhecido, preserva-a e classifica-a como tal, de forma auditável. Um valor por
omissão ou derivado só é legítimo se estiver definido no contrato aplicável: verifica e testa
essa regra, mantendo distinguíveis a ausência original, a proveniência e o valor obtido quando
forem relevantes para a decisão. Regista o instante da observação separadamente do timestamp
da fonte; observar agora não prova frescura da fonte. Um valor por omissão ou derivado não
fabrica timestamp da fonte, frescura, estado validado, aprovação, cobertura observada ou prova
de recuperação. Também não apaga evidência negativa: no caso de
[references/mapa-de-fronteiras.md](references/mapa-de-fronteiras.md), a qualidade inválida
observada antes do descarte continua a bloquear segundo aquele contrato.

**9. Como se desfaz, e o desfazer foi testado?**
Verifica o rollback aplicável, incluindo hashes, modos e estado. Confirma também que uma nova
tentativa consegue arrancar depois dele; um diretório de estado novo por tentativa é uma
opção, não um requisito universal. Nas remoções, volta a verificar as proteções no momento de
apagar e considera quarentena. O que não tem rollback é declarado como tal.

**10. Que passos humanos ficam por fazer, e estão escritos?**
Credenciais a criar, permissões mínimas, onde guardar segredos sem chat nem argv, decisões que
só o dono pode tomar. Entrega as instruções junto com o PR, não depois de alguém perguntar.

## Como entregar o resultado

No corpo do PR ou do handoff, acrescenta uma secção curta "Modos de falha considerados", com
uma linha por pergunta relevante: o risco, o que fizeste e como está provado (o teste, a prova
contra o host ou o dryrun). Marca o que fica por provar e quem o prova. Isto não substitui a
revisão independente. Serve para o revisor discutir o que é difícil, não o que era previsível.

Quando houver fronteiras entre componentes, inclui o mapa e o resultado do traço adversarial,
com o último efeito observado. Separa percursos completos de componentes testados à parte e
ligações por provar; não juntes essas provas numa alegação de recuperação completa.

Para um exemplo da secção e de como chegar a ela, lê
[references/exemplo-seccao-pr.md](references/exemplo-seccao-pr.md).

## Sinais de que a autorrevisão foi superficial

- Todas as respostas são "os testes passam".
- A verificação pós-instalação só confirma que algo está "ativo".
- O teste do consumidor usa uma fixture construída à mão na fronteira cuja ligação se pretende provar.
- As suposições relevantes sobre dados reais ou ambiente alvo não foram verificadas nem marcadas por provar.
- O PR não diz o que o humano tem de fazer a seguir.

## Quando não aplicar

Alterações sem efeito operacional (documentação, renomeações internas sem mudança de
comportamento, testes puros). Scripts de uso único corridos sob supervisão humana não ativam
esta skill automaticamente. Podem reutilizar perguntas relevantes, sobretudo a 3, a 7 e a 9;
a relevância da 2 e da 6 depende do custo, das repetições e dos efeitos do script.
