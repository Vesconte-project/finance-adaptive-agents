---
name: independent-review-of-agent-work
description: Rever um PR, bloco privilegiado, leitor ou relatório produzido por outro agente antes de o dono aprovar, fazer merge ou correr em produção. Usa para verificar afirmações em vez de as aceitar, comparar com a base relevante, verificar evidência autorizada e devolver um veredito acionável. Não para a autorrevisão de quem escreveu nem para revisões de estilo.
---

# Revisão independente do trabalho de outro agente

O autor escreve "77 testes passaram", "só leitura", "sem conflitos", "pronto para merge". O
revisor não está ali para concordar: está para que o dono possa decidir sem ter de confiar
cegamente. Uma revisão útil reproduz o que importa, procura o que o autor não viu e devolve um
veredito que diz o que bloqueia, o que é só para saber e o que o humano tem de fazer.

**Evidência.** Revisões de PRs, blocos root e leitores numa plataforma com um único host,
2026-10. Ver os casos em [references/casos-2026-10.md](references/casos-2026-10.md).

## Método

1. **Fixa o objeto.** Usa um identificador imutável: SHA do código, hash do bloco ou versão
   com digest do relatório. Num PR, confirma a base Git; quando a conclusão depende do que
   está instalado, compara também essa versão, se houver evidência disponível.
2. **Lê o artefacto, não apenas a descrição.** Num PR, lê o diff do código antes dos testes;
   num relatório, confronta afirmações e fontes. Para blocos e leitores, procura escritas,
   chamadas de rede, leitura de segredos ou valores confidenciais e o que sai para o ecrã.
   Verifica as salvaguardas aplicáveis, como identidade efetiva, transação READ ONLY e saída
   por allowlist. O rótulo "só leitura" não prova segurança nem concede acesso.
3. **Reproduz as afirmações que decidem.** Executa código candidato apenas num ambiente
   isolado apropriado, com as ferramentas e autorizações existentes. Usa condições limpas e
   sem rede quando adequadas ao teste; se falhar, distingue a causa ambiental de um defeito.
   Uma verificação no host exige autorização e salvaguardas próprias: não transfiras para
   produção código candidato só por se declarar leitor. Na falta de acesso, pede evidência
   adequada e declara o limite. Escolhe provas dirigidas e verifica recibos existentes;
   não repitas suites integrais por rotina. Para ordenar provas caras e reutilizar evidência,
   lê [references/validation-evidence-reuse.md](references/validation-evidence-reuse.md).
4. **Verifica a seleção quando a mudança decide o que é processado.** Quando necessário e
   autorizado, pede ou executa uma simulação fixada ao candidato que identifique entradas,
   saídas e bloqueios. Um dryrun não garante ausência de escritas: verifica o percurso e as
   salvaguardas antes da execução. Usa dados reais apenas com acesso autorizado e saída
   permitida; sem isso, regista o que a prova sintética ou sanitizada não demonstra. Investiga
   saídas não justificadas e revalida quando o candidato ou o contexto relevante mudar.
5. **Olha para os lados, quando aplicável.** Havendo PRs concorrentes, verifica sobreposição,
   integração e ordem de merge; usa `git merge-tree` se disponível e adequado. Se existir
   deploy associado, verifica gates e janelas relevantes. Num relatório ou bloco sem estes
   mecanismos, assinala que não se aplicam; a sua ausência não é um defeito.
6. **Pergunta pelos modos de falha.** Falha parcial que bloqueia tudo, custo sem trabalho,
   verificação que só prova existência, ausência de dado a fabricar dado, rollback testado e
   passos humanos em falta. Lê cada caminho de erro como se fosse acontecer amanhã.
7. **Separa o veredito em três listas.** O que **bloqueia** (com o risco concreto e o teste ou
   prova que o resolve), o que é **para saber** (limites aceitáveis, documentar) e o que o
   **humano tem de fazer** (credenciais, decisões, quando fazer merge). Termina com uma decisão
   clara: aprovado, aprovado com condições, ou não aprovado e porquê.
8. **Escreve a mensagem de volta ao autor**, autossuficiente: o identificador revisto, o que está bem
   numa linha, as correções numeradas com os testes esperados e o que não fazer. Sem pedir
   mais do que o necessário para a decisão.

Para o modelo do veredito, da mensagem de volta e das regras de severidade, lê
[references/modelo-veredito.md](references/modelo-veredito.md).

## O que a revisão não faz

Não aprova o que não leu nem o que não conseguiu reproduzir; nesse caso diz isso mesmo. Não
alarga o âmbito do PR com melhorias opcionais e chama-lhes bloqueios. Não reescreve o trabalho
do autor em vez de o devolver. Não ganha autoridade por rever: o merge e a instalação continuam
a ser decisões do dono.

## Sinais de uma revisão fraca

- O veredito repete a descrição do autor.
- Não identifica o objeto nem distingue provas verificadas de afirmações do autor.
- Omite a base instalada ou PRs paralelos quando influenciam a decisão.
- Omite limites de verificação ou passos humanos necessários; se não existirem, diz isso.
- Repete suites completas sem dizer que mudança ou dúvida nova essa repetição esclarece.

## Quando não aplicar

Mudanças triviais sem efeito operacional, onde uma leitura rápida basta. Não imponhas este
processo a uma revisão de estilo ou redação.
