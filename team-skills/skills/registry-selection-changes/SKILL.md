---
name: registry-selection-changes
description: Rever ou alterar o código que escolhe uma linha por entidade num registo com linhas duplicadas (supersessions, aliases, rejeições, remoções) ou que acrescenta um filtro de exclusão sobre esse registo. Usa antes de fazer merge de uma mudança de resolução/filtro que decide que entidades um pipeline processa. Não para desenho de esquema de raiz.
---

# Mudanças à seleção de entidades num registo com duplicados

Um registo de entidades (tickers, clientes, produtos) acumula várias linhas por entidade:
a linha canónica ativa, linhas antigas marcadas como substituídas por um reconciliador,
rejeições de validação e pedidos de remoção. O código que reduz isto a "uma linha por
entidade" decide o que o pipeline processa. Um erro aqui não falha: **faz entidades
desaparecerem em silêncio**.

**Evidência.** Um pipeline de mercado, 2026-07 a 2026-10. O reconciliador marcava a linha
antiga como `superseded_by:<chave da nova>` microssegundos **depois** de gravar a ativa. O
loader ficava com a linha de `updated_at` mais recente. Durante meses isso não teve efeito.
Uma alteração posterior passou a excluir linhas `rejected` do refresh e 58 entidades
(incluindo as maiores do universo) deixaram de receber dados, sem retenção nem alerta. A
primeira correção, que tratava qualquer rejeição como veto, teria excluído outras 8 que
funcionavam. Foi uma prova contra os dados reais, antes do merge, que o apanhou.

## Regras de decisão

1. **Nunca "a mais recente vence".** `updated_at` regista a última escrita, não a
   autoridade. Uma desativação, uma migração ou um backfill podem tocar numa linha antiga
   depois da canónica. Resolve por proveniência estruturada e identidade, com empates
   ordenados por chaves estáveis, não por tempo.
2. **Uma supersession só é autoridade se for verificável.** Aceita-a quando a origem é
   estruturada (marca do reconciliador, não texto livre), o motivo corresponde ao alvo e
   o alvo existe, é único, é elegível e é a mesma entidade. Uma supersession que aponta para
   nada é um aviso, não uma exclusão.
3. **Só uma remoção explícita exclui uma entidade com linha ativa elegível.** Uma rejeição
   de validação antiga, um onboarding falhado ou uma origem desconhecida ao lado de uma
   ativa válida são **conflitos a reportar**, não vetos. Exclui sem ativa elegível ou com
   marcador de remoção explícito.
4. **Exclusão visível.** Cada entidade do universo que saia do processamento por estado do
   registo é contada, gravada num registo durável e alertada. "Excluída" e "retida" são
   estados que alguém vê; "não pedida" não pode ser silencioso.
5. **Um filtro novo ativa dados antigos.** Antes de acrescentar uma exclusão por estado
   (`rejected`, `inactive`…), mede quantas entidades do universo atual passam a ser
   excluídas e porquê. O defeito de dados pode estar latente há meses e só o filtro o
   torna visível.

## Prova obrigatória antes do merge: diff de seleção com dados reais

Testes sintéticos não conhecem os padrões que o registo real acumulou. Com autorização e
só em leitura, corre o loader e o resolver **do head do PR** contra o registo real (a
mesma identidade e o mesmo SELECT que o worker usa, numa transação só de leitura) e
compara com o código instalado:

- entidades que **entram** e que **saem**, por região ou partição;
- contagens de decisão (ativa, excluída, por validar, ambígua ou bloqueada) e códigos;
- impacto em qualquer orçamento ou limiar que conte entidades bloqueadas;
- prova de acesso às colunas novas que o SELECT lê.

Critério: as entradas esperadas entram, **as saídas são zero ou cada uma tem uma
justificação explícita**, e não há bloqueios inesperados. Repete a prova a cada head novo.
A saída só leva identificadores públicos, contagens e códigos, nunca chaves internas, notas
livres nem valores de negócio.

## Limpeza de dados não substitui a correção

Apagar as linhas antigas parece mais simples, mas o padrão volta a cada mudança de
identidade, e essas linhas podem ser histórico de que outras partes dependem. Corrige
primeiro a resolução. Trata a limpeza como uma operação revista à parte: inventário de
referências, decisão linha a linha, backup e rollback. Corrige também o escritor (por
exemplo, a linha substituída nunca pode ficar mais recente do que a ativa).

## Sinais de alerta

- O número de entidades processadas desce sem nenhuma retenção ou falha registada.
- Entidades grandes ou bem conhecidas com o último dado parado numa data comum.
- Um PR que "só alinha exclusões" com o estado do registo.
- Uma regra de veto que não distingue a remoção explícita das outras rejeições.

## Quando não aplicar

Registos com uma linha garantida por entidade (restrição única aplicada pela base) e sem
estados de ciclo de vida. Mesmo aí, a regra da exclusão visível continua útil.
