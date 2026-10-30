---
name: availability-holds-from-provider-signals
description: Rever ou corrigir a lógica que marca entidades como retidas ou atrasadas a partir de respostas de um fornecedor externo (preço diário, cotação, histórico) e um orçamento de retenções que pode falhar uma região inteira. Usa quando muitas entidades ficam retidas de repente, quando um orçamento rebenta sem perda de dados ou ao acrescentar um sinal novo ao gate.
---

# Retenções a partir de sinais do fornecedor

Um pipeline que pede dados a um fornecedor marca uma entidade como retida quando a
resposta parece atrasada, incompleta ou falhada. Um orçamento ("no máximo N ou X% retidas
por região") protege contra publicar uma região estragada. Se os sinais forem ruidosos, o
orçamento falha regiões **sem que falte nenhum dado**.

**Evidência.** Um pipeline de mercado com yfinance, 2026-10:
- uma região de 83 entidades teve 74 retidas; 64 tinham só "cotação atrasada" com o preço
  diário da sessão fresco, e a região falhou inteira;
- uma run agregada à meia-noite marcou 510 entidades como "preço atrasado" porque a resposta
  re-obtida, depois da normalização, terminava na véspera. A linha da sessão esperada já
  estava publicada e validada por uma run anterior, 90 minutos antes, por isso não faltava
  nenhum dado.

## Regras de decisão

1. **Classifica cada sinal pela consequência.** Uma cotação intradiária atrasada, com o
   preço diário validado da mesma sessão fresco, é um **aviso**, não uma retenção. Só
   retém o que impede publicar dados corretos.
2. **Compara datas na sessão da bolsa, não em UTC.** Converte timestamps do fornecedor para
   a data local da bolsa antes de os comparar com a sessão esperada. Campos epoch vêm em
   segundos, não em nanossegundos. Um timestamp ausente fica ausente: nunca substituas por
   "agora", porque isso fabrica frescura.
3. **Não deixes uma re-obtenção desfazer dados já validados.** Se a resposta termina antes
   da sessão esperada mas a chave `(entidade, sessão)` já existe validada no armazenamento
   canónico, isso é uma regressão do fornecedor: aviso e contagem, sem retenção e sem tocar
   no dado guardado. Mantém a regra inversa para retenções verdadeiras: a presença em cache
   não limpa sozinha uma retenção que tem uma causa própria.
4. **Uma linha descartada na normalização tem de ficar registada.** Se a normalização remove
   linhas (data ou fecho nulos), regista por entidade a última data bruta do índice, o fuso
   e a contagem de linhas descartadas, sem valores. Sem isto não se distingue "o fornecedor
   não tinha o dia" de "tinha mas vinha vazio".
5. **O orçamento conta causas, não sintomas.** Antes de mudar um limiar, separa as retenções
   por motivo e confirma, numa amostra, se os dados existem no canónico. Não baixes o
   limiar nem acrescentes tolerância sem identificar a transformação que gerou o sinal.
6. **Uma falha do orçamento não se pode perder.** Se o fluxo agregado captura a exceção do
   orçamento para continuar outras fases, garante que a volta a lançar mesmo quando uma fase
   posterior falha primeiro, e que o alerta sai antes.

## Diagnóstico rápido quando muitas retenções aparecem

1. Separa por motivo (cotação, preço, histórico ou pedido falhado) e por run (regional ou
   agregada, e a hora).
2. Para 2–3 entidades do grupo, em leitura: existe a linha canónica da sessão esperada? Quem
   a escreveu, e quando? O que diz o diagnóstico da resposta normalizada?
3. Compara as janelas pedidas (início, fim e fim exclusivo do fornecedor) entre a run que
   funcionou e a que reteve.
4. Só depois decide a correção: sinal mal classificado, comparação de datas, regressão do
   fornecedor ou retenção verdadeira.

## Quando não aplicar

Fontes internas com contrato de entrega garantido, ou gates sem orçamento agregado. A
regra 2 (datas na sessão local) aplica-se sempre que se comparam datas de mercado.
