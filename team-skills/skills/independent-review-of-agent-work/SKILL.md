---
name: independent-review-of-agent-work
description: Rever um PR, bloco privilegiado, leitor ou relatório produzido por outro agente antes de o dono aprovar, fazer merge ou correr em produção. Usa para verificar afirmações em vez de as aceitar, comparar com o que está instalado, provar com dados reais e devolver um veredito acionável. Não para a autorrevisão de quem escreveu nem para revisões de estilo.
---

# Revisão independente do trabalho de outro agente

O autor escreve "77 testes passaram", "só leitura", "sem conflitos", "pronto para merge". O
revisor não está ali para concordar: está para que o dono possa decidir sem ter de confiar
cegamente. Uma revisão útil reproduz o que importa, procura o que o autor não viu e devolve um
veredito que diz o que bloqueia, o que é só para saber e o que o humano tem de fazer.

**Evidência.** Revisões de PRs, blocos root e leitores numa plataforma com um único host,
2026-10. Ver os casos em [references/casos-2026-10.md](references/casos-2026-10.md).

## Método

1. **Fixa o objeto.** Trabalha sobre um SHA exato (o head do PR, ou o hash do bloco selado),
   nunca sobre "a branch". Confirma a base: de que commit parte e se esse commit é o que está
   instalado. Um PR feito sobre um main antigo pode estar certo e entrar errado.
2. **Lê o código, não a descrição.** Lê o diff do código de produção primeiro e os testes
   depois. Para blocos e leitores, procura escritas, chamadas de rede, leitura de segredos ou de
   valores confidenciais, e o que sai para o ecrã. "Só leitura" verifica-se: transação READ
   ONLY, identidade efetiva, SELECTs fixos e saída por allowlist.
3. **Reproduz as afirmações que decidem.** Corre os testes num ambiente limpo e sem rede. Se
   falharem, descobre se o problema é teu (permissões, umask, TMPDIR em tmpfs) ou do código,
   antes de concluir. Confirma os hashes contra o Git. Corre no host, só em leitura, a parte do
   código que depende do ambiente (inventários, tipos de filesystem).
4. **Testa contra o estado real quando a mudança decide o que é processado.** Pede ou corre um
   dryrun fixado ao head, contra os dados reais, que diga quem entra, quem sai e quem fica
   bloqueado. Exige zero saídas não justificadas. Repete a cada head novo.
5. **Olha para os lados.** Há outros PRs abertos que tocam nos mesmos ficheiros? Testa a junção
   (`git merge-tree`) e diz a ordem de merge. Há um merge recente que mude o contexto (por
   exemplo, um motor de deploy novo que adia pedidos)?
6. **Pergunta pelos modos de falha.** Falha parcial que bloqueia tudo, custo sem trabalho,
   verificação que só prova existência, ausência de dado a fabricar dado, rollback testado e
   passos humanos em falta. Lê cada caminho de erro como se fosse acontecer amanhã.
7. **Separa o veredito em três listas.** O que **bloqueia** (com o risco concreto e o teste ou
   prova que o resolve), o que é **para saber** (limites aceitáveis, documentar) e o que o
   **humano tem de fazer** (credenciais, decisões, quando fazer merge). Termina com uma decisão
   clara: aprovado, aprovado com condições, ou não aprovado e porquê.
8. **Escreve a mensagem de volta ao autor**, autossuficiente: o SHA revisto, o que está bem
   numa linha, as correções numeradas com os testes esperados e o que não fazer. Sem pedir
   mais do que o necessário para a decisão.

## O que a revisão não faz

Não aprova o que não leu nem o que não conseguiu reproduzir; nesse caso diz isso mesmo. Não
alarga o âmbito do PR com melhorias opcionais e chama-lhes bloqueios. Não reescreve o trabalho
do autor em vez de o devolver. Não ganha autoridade por rever: o merge e a instalação continuam
a ser decisões do dono.

## Sinais de uma revisão fraca

- O veredito repete a descrição do autor.
- Nenhum teste foi corrido e nenhum hash foi conferido.
- Não menciona a base instalada nem os PRs paralelos.
- Não diz quando fazer merge nem o que o humano tem de fazer.

## Quando não aplicar

Mudanças triviais sem efeito operacional, onde uma leitura rápida basta. Mesmo aí, confirma o
SHA e a base.
