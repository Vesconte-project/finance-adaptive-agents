# Exemplo completo: secção "Modos de falha considerados"

Exemplo para um PR que acrescenta um emissor de estado de deploys para o GitHub (um timer de
60 s, um passo root que resume o estado e um emissor sem privilégios). É o tipo de secção que
teria evitado três correções na revisão.

```markdown
## Modos de falha considerados

| # | Risco | O que fiz | Prova |
|---|---|---|---|
| 1 | Um componente com estado inválido impede a publicação dos outros | O resumo regista um erro por componente e sai 0; o emissor corre sempre e salta só o componente inválido | teste `test_one_invalid_component_does_not_block_others` |
| 1 | Colisão de lock com um deploy a decorrer | `LOCK_NB` falha só esse componente nesse ciclo; repete no seguinte | teste `test_lock_busy_retries_next_cycle` |
| 2 | Um token e um JWT pedidos a cada minuto sem nada novo | O token só é pedido se houver estado por entregar ou por reconciliar | teste: 10 ciclos sem mudanças = 0 chamadas à API |
| 3 | A instalação só prova que o timer existe | A verificação exige um ciclo real: resumo OK e ≥1 componente delivered/already-delivered; senão, rollback | teste do instalador com um simulador estrito da API |
| 5 | O host difere do CI (tmpfs, units template, versão do openssl) | Prova do host só de leitura, fixada ao SHA; admissão igual em plan e apply | relatório da prova, perfil `0b4a…` |
| 6 | Um evento atrasado sobrepõe um estado mais novo | Checks imutáveis por (pedido, geração); nunca PATCH | teste `test_old_generation_cannot_overwrite` |
| 6 | Um check vermelho antigo continua visível depois de um sucesso | Aceite; documentado em RELEASE_GITHUB_VISIBILITY.md | — |
| 7 | Uma falha de envio fica invisível | Outbox durável, código impresso por componente; o Healthchecks continua a ser o alarme | teste da outbox |
| 8 | Um campo em falta interpretado como sucesso | Sem `updated_at` → usa o instante da observação e marca-o; estado desconhecido → `unknown`, nunca `verified` | teste de validação |
| 9 | Uma instalação parcial | Snapshot e rollback automático verificados por hash; diretório de estado por tentativa | teste com falha injetada depois do 1.º ficheiro |
| 10 | O dono tem de criar uma credencial | Instruções: GitHub App só com Checks: write, instalada nos 5 repositórios; chave por prompt escondido | `docs/…/INSTALL.md` §2 |

**Por provar:** o custo real em memória no host (medido na primeira semana) e a receção dos
checks pela App verdadeira (no ciclo de verificação da instalação).
```

## Como chegar a esta tabela

- Percorre as 10 perguntas com o diff aberto. Para cada uma, escreve primeiro o pior caso
  concreto ("o deploy do data-ops está a meio e segura o lock") e só depois a defesa.
- Se a resposta for "não se aplica", escreve porquê numa linha. Um "não se aplica" sem motivo
  costuma esconder um risco.
- Cada defesa tem de apontar para uma prova que outra pessoa consiga repetir: um teste com nome,
  um relatório com hash ou um dryrun com data. "Revi com cuidado" não é prova.
- O que não conseguires provar vai para "Por provar", com quem o prova e quando. É informação
  útil para o revisor, não uma fraqueza do PR.
