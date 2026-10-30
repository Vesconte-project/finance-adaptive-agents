---
name: bounded-memory-batch-builders
description: Corrigir ou rever um builder/ETL noturno ou um passo de publicação cuja memória cresce com o histórico total (leitura de tabelas inteiras, comparações por janela min/max, upserts de listas completas) e chega ao limite do cgroup ou é morto por OOM. Usa para desenhar a versão em streaming e a prova de memória antes do merge; não para escolher MemoryMax.
---

# Builders em lote com memória limitada

Um builder que funcionava quando o histórico era pequeno passa a ser morto por OOM
quando os dados crescem, sem nenhuma alteração de código. Subir o limite de memória adia
o problema; a correção é a memória depender do tamanho do lote, não do histórico.

**Evidência.** Um worker com cgroup de 2 GiB e 256 MiB de swap, 2026-10:
- um builder de eventos de resultados lia duas tabelas inteiras com `mappings().all()`,
  copiava tudo para dicts, agrupava e ordenava em memória e fazia upsert da lista
  completa. Foi morto por OOM 39 s depois de arrancar, a seguir a outra fase pesada;
- a versão em streaming manteve resultados idênticos e baixou o pico para cerca de
  160 MiB com 1,6 M observações;
- noutro worker, uma comparação de preços antes da publicação lia "todas as entidades do
  lote entre a data mínima e a máxima do lote". Um lote misturava uma linha antiga de uma
  entidade com as de hoje de centenas, e essa janela retangular puxava quase a tabela
  inteira (1,6 M linhas para 6 históricos). Pedir só as chaves exatas do lote baixou o pico
  de 2,4 GiB para 0,4 GiB.

## Padrões que crescem com o histórico

- `fetchall()`/`.all()`/`read_table()` de uma tabela ou cache inteira para filtrar depois.
- Uma janela de comparação construída com o min/max de um lote heterogéneo: um retângulo
  `entidades × [data mínima, data máxima]` em vez das chaves `(entidade, data)` do lote.
- Agrupar, deduplicar ou ordenar coleções inteiras em Python quando a base podia ordenar.
- Upsert de uma lista completa numa chamada.
- Ler um ficheiro colunar inteiro para obter resumos (máximos, contagens, presença).

## Desenho em streaming

1. **Cursor do lado do servidor** com partições limitadas (por exemplo, 500–5 000 linhas).
   Num driver que precisa de transação para cursores com nome, abre-a explicitamente.
2. **Ordena na base pela identidade de deduplicação**, de forma que todas as linhas da mesma
   identidade cheguem contíguas. Depois reduz em streaming (`groupby`) com a mesma regra de
   escolha do código antigo. Atenção à normalização: se a identidade em Python usa
   `strip()`/`upper()`, ordena pelo mesmo valor normalizado e com uma collation binária
   (`COLLATE "C"`), ou os grupos partem-se.
3. **Escreve em lotes fixos** dentro da mesma transação que o código antigo usava. O
   streaming não pode mudar a atomicidade nem a semântica de "último escritor" quando duas
   identidades colidem.
4. **Comparações por chave exata:** junta com `unnest(chaves[])`, ou equivalente, em vez de
   janelas retangulares; limita o número de chaves por pedido.
5. **Resumos colunares em lotes** (`iter_batches`), guardando só o agregado por entidade.
6. **Uma interrupção nunca fecha como sucesso:** captura `BaseException` para marcar o build
   como falhado e volta a lançá-la.

## Prova antes do merge

- **Equivalência:** os mesmos resultados que o código antigo (fingerprint de linhas
  completas) em dados sintéticos com os padrões difíceis: duplicados entre fronteiras de
  lote, empates, normalização de identificadores e colisões entre fontes.
- **Volume proporcional à produção**, não um exemplo pequeno. Calibra as contagens com
  números reais da produção (só contagens).
- **No mesmo processo e depois da fase anterior:** mede o RSS máximo do processo que
  executa, depois de correr a fase pesada que o precede, porque a memória retida soma.
  Define a meta com folga face ao limite (por exemplo, < 50% do cgroup).
- **Base real descartável** (PostgreSQL em contentor, sem rede) para provar cursores,
  transações e o rollback numa interrupção.
- **Ledger:** confirma o estado do registo de build quando o processo é morto a meio.

## Sinais de alerta

- OOM sem traceback, ou um erro de pipe "worker saiu sem resultado" num subprocesso.
- Um pico de memória do cgroup numa fase que processou poucas entidades (amplificação).
- Memória a crescer de semana para semana com o mesmo número de entidades.

## Quando não aplicar

Tabelas pequenas e limitadas por desenho, ou passos em que a carga completa é exigida pelo
algoritmo e cabe com folga medida. Nesses casos, documenta o limite e mede-o.
