# Exemplo completo e modelo de investigação

## Exemplo: 58 entidades sem dados desde uma data

| Passo | O que se fez | Resultado |
|---|---|---|
| 1. Datar | Último preço canónico por entidade afetada | 49 entidades paradas a 23/10 (sexta) e 3 de outra bolsa também a 23/10 |
| 2. O que mudou | `git log --first-parent` do repositório de ingestão e recibos de deploy entre 23/10 e 26/10 | Um merge a 24/10 às 15:45 UTC passou a excluir entidades com o estado `rejected` |
| 3. Alcance | Entidades afetadas vs não afetadas; o que têm em comum | As 52 afetadas sem evento de retenção eram **exatamente** as 52 com linhas duplicadas no registo (ativa + rejeitada) |
| 4. Escada de evidência | Contagens, depois a origem das linhas rejeitadas (só códigos estruturados), depois o `updated_at` relativo | As rejeitadas eram supersessions de julho, gravadas 8–32 µs depois da ativa; o loader escolhe a mais recente |
| 5. Porquê agora | Antes do merge, `rejected` não excluía; depois, a linha errada passou a excluir | Condição latente (julho) + gatilho (merge de 24/10) |
| 6. Corrigir a causa | Resolução por proveniência e identidade, sem precedência por tempo; exclusões contadas e alertadas | Dryrun com o registo real: 58 entram (6 a mais do que as conhecidas), 0 saem |
| 7. Provar com o real | Depois do deploy, datas canónicas das afetadas | 26–30/10 preenchidos sozinhos pela recuperação automática |

O que **não** se fez: apagar as linhas antigas (o padrão volta e podem ser histórico), voltar
atrás no merge (a exclusão de rejeitadas era correta para remoções reais) ou recuperar os dados
à mão antes de a correção estar instalada.

## Modelo de nota de investigação

```markdown
**Sintoma:** <o que se vê, com números>
**Último bom / primeiro mau:** <data/hora> / <data/hora> (fonte: …)
**Mudanças na janela:** <merges, deploys, config, dados, volume, horário> — fonte de cada uma
**Afetados vs não afetados:** <contagens; característica comum; coincidências exatas>
**Evidência (por degrau):**
1. Contagens: … (leitor `<hash>`)
2. Amostras: … (2–3 casos, só datas e códigos)
3. Origem: … (quem escreveu, quando, com que código)
**Condição latente:** …
**Gatilho:** …
**Porque é que antes não falhava:** …
**Correção da causa:** … (PR, prova contra os dados reais)
**Sintoma/recuperação:** … (operação separada, depois da correção instalada)
**Visibilidade acrescentada:** … (para não voltar a ser silencioso)
**Por provar:** …
```

## Perguntas que desbloqueiam uma investigação parada

- Qual é o último dia em que funcionou, e o que entrou entre esse dia e o seguinte?
- Os afetados têm alguma coisa que os não afetados não têm?
- O que mudou de tamanho (volume, histórico, número de entidades) desde que funcionava?
- A hora de execução mudou, ou o comportamento externo varia com a hora?
- Se a hipótese estiver certa, que outro sinal devia existir, e existe?
