# Exemplo: secção "Modos de falha considerados"

Exemplo ilustrativo para um PR que acrescenta um emissor periódico de estado de deploys a
um serviço externo: um passo privilegiado resume o estado e um emissor sem privilégios faz
a entrega. A tabela mostra a forma do resultado; os testes e relatórios citados devem existir
na entrega real. Este pacote não fornece uma suite executável nem prova a instalação.

## Modos de falha considerados

| # | Risco | Defesa proposta | Prova a ligar na entrega |
|---|---|---|---|
| 1 | Um componente inválido impede a publicação dos outros | O resumo conserva um erro por componente; o emissor continua com os válidos e torna a falha visível | Teste com um componente inválido e outro entregue |
| 1 | Colisão de lock com um deploy | O lock ocupado adia apenas esse componente; há nova tentativa | Teste de colisão e tentativa seguinte |
| 2 | Autenticação externa em cada ciclo sem trabalho | Pedir token apenas quando houver entrega ou reconciliação necessária | Teste de ciclos sem mudanças, com zero chamadas externas |
| 3 | A instalação só prova que o timer existe | Exigir um ciclo com efeito observado e definir a resposta a falha | Teste do instalador com simulador estrito da API; receção real por provar |
| 5 | O ambiente difere do CI | Confirmar apenas suposições relevantes, com leitura autorizada do alvo; neste processo com plan/apply, alinhar admissão e revalidar condições mutáveis | Relatório ligado à revisão e ao alvo; sem acesso, marcar por provar |
| 6 | Evento atrasado sobrepõe estado mais novo | Neste desenho, checks imutáveis por pedido e geração | Teste com eventos fora de ordem |
| 6 | Falha antiga continua visível depois de sucesso | Explicar a coexistência e como identificar a geração atual | Exemplo de apresentação e limitação documentada |
| 7 | Falha de envio fica invisível | Outbox durável, código por componente e canal de alerta definido | Teste de falha, persistência e nova tentativa |
| 8 | Timestamp ausente fabrica frescura | Sem `updated_at`, manter o timestamp da fonte ausente/desconhecido; guardar o instante da observação num campo separado. Estado desconhecido nunca passa a `verified` | Teste que distingue tempo da fonte, tempo de observação e estado |
| 9 | Instalação parcial ou segunda tentativa bloqueada | Snapshot e rollback verificados; neste desenho, diretório de estado por tentativa | Falha injetada após a primeira alteração, restauro e nova tentativa |
| 10 | Operador precisa de criar uma credencial | Documentar permissões mínimas, âmbito da instalação e canal seguro para a chave | Instruções revistas, sem valores secretos |

**Por provar:** consumo de memória no alvo e receção pelo serviço externo real. Na entrega,
identificar o responsável por cada verificação, a condição de acesso autorizado e o momento
em que poderá ocorrer. O simulador não prova a receção real.

## Como chegar a esta tabela

- Percorre as dez perguntas com o diff aberto. Escreve primeiro o pior caso concreto, como
  "um deploy mantém o lock ocupado", e só depois a defesa.
- Se a resposta for "não se aplica", escreve porquê. Uma dispensa sem motivo pode esconder risco.
- Liga cada defesa a uma prova inspecionável: teste, relatório ou dryrun identificado. Um hash
  identifica conteúdo; não demonstra por si só que a conclusão é correta.
- Não copies alegações da tabela como trabalho concluído. Usa resultados realmente observados
  e marca propostas e verificações pendentes como tal.
- Quando a decisão atravessar componentes, acrescenta o mapa e o traço de
  [mapa-de-fronteiras.md](mapa-de-fronteiras.md), indicando o último efeito observado.
- Leva para "Por provar" o que não foi observado, com responsável e condição de verificação.
  Não obtenhas acesso nem executes operações só porque aparecem neste exemplo.
