# Manutenção após as avaliações independentes

Foram corrigidas **16 das 38 skills**, preservando os IDs, os âmbitos do catálogo e o conhecimento técnico útil. Os pareceres dos modelos foram tratados como achados a verificar e decisões a justificar. Não foram alterados o seletor, o avaliador nativo, os contratos de admissão ou os metadados do catálogo.

## Validação das 16 skills alteradas

Cada pacote final foi avaliado pelo comando real do repositório:

```bash
PYTHONPATH=src .venv/bin/python -m finance_adaptive_agents.team_skills validate SKILL_ID --selector SELECTOR
```

| Seletor | Ready | Needs revision |
| --- | ---: | ---: |
| Codex | 16 | 0 |
| Copilot, Sonnet solicitado | 14 | 2 |
| Claude Code, Opus solicitado | 16 | 0 |

Foram feitas 63 tentativas, incluindo reavaliações depois de correções. O índice final contém 48 pareceres correspondentes exatamente aos digests atuais. Uma resposta Copilot com JSON inválido foi preservada como indisponível; a repetição completou normalmente. O avaliador não foi enfraquecido para aceitar essa resposta.

Foram solicitados `claude-sonnet-5.5` e `claude-opus-5-5` através das variáveis de ambiente de cada subprocesso. A saída analisada pelo avaliador não conserva metadados que atestem o modelo por resposta. O modelo Codex ficou no default nativo, sem pin explícito. Esta comparação não é um benchmark controlado.

## Correções principais

- Exemplos executáveis: nomes de symlinks escapados, falhas de enumeração/resolução inconclusivas, inventário Git sem URLs/segredos, commit ausente explícito, distinção SSH entre paths relativos e absolutos e validação integral antes de emitir resultados.
- Observação: falhas de leitura não viram listas vazias; um download falhado não permite usar um schema antigo; a inspeção de fontes systemd evita redigir conteúdo de units com filtros por linha.
- Operação: readiness ligada à nova instância e release, identidade de build e colisões, consultas Prefect com cobertura explícita, autorização e canary em upgrades, inventário de units carregadas e instaladas, defaults OOM e limpeza de sondas conforme o mecanismo real.
- Contratos: recibos ligados a inputs/configuração e protegidos contra reutilização indevida, opções Stripe validadas no servidor, DNS por challenge com RRsets multivalor e paragem perante gates sem suporte.
- Clareza: catálogo de diagnóstico reparado para 18 entradas detalhadas, âmbito de planeamento/execução alinhado, proveniência histórica explícita e remissões para outras skills marcadas como opcionais onde necessário.

O detalhe por skill está em `maintenance_changes` no [relatório JSON](SKILL_CROSS_MODEL_MAINTENANCE_RESULTS.json).

## Provas executadas

A regressão passou com **225 testes, zero falhas e zero skips**: 32 casos novos exercitam os exemplos distribuídos nas skills. As 16 skills passaram `quick_validate`; todas as referências Markdown locais existem e `git diff --check` passou. A última alteração posterior à regressão apenas clarifica a secção de upgrades Prefect; a estrutura e os três pareceres nativos foram verificados novamente sobre esse conteúdo final.

Um revisor independente, sem histórico e sem ler os testes ou relatórios anteriores, criou os seus próprios fixtures. Encontrou três falhas adicionais: colisão de paths SSH, erro systemctl escondido e comparação com schema antigo após falha curl. Repetiu os mesmos fixtures e confirmou as três correções. O caso de continuação de uma unit foi depois reproduzido num teste a partir de um achado do Copilot.

Não foram testados hosts reais, alterações DNS, pagamentos, migrações, restarts de produção ou credenciais reais. Os pareceres textuais e os testes sintéticos têm esses limites.

## Desacordos preservados e decisão

O Sonnet mantém `needs_revision` em duas das skills alteradas:

- `guards-that-pass-blindly`: pede apagar relatos operacionais ou convertê-los em exemplos hipotéticos. Os relatos estão delimitados como contexto; converter história em hipótese falsificaria a proveniência. Mantive-os.
- `jira-data-center-operations`: pede retirar a nota que identifica um padrão como relato da origem, sem teste atual verificável. A nota torna a limitação explícita e continua a exigir confirmação na instância alvo. Mantive-a.

Não considero estes dois pedidos bloqueios técnicos. Também não renomeei IDs estáveis apenas por preferência de um avaliador. A versão final de `orchestrator-runtime-ops`, com descrição restrita a Prefect e autorização/canary explícitos, recebeu `ready` dos três seletores.

No catálogo completo, combinando os 16 pacotes reavaliados com os **22 inalterados e com digest confirmado**, os pareceres mais recentes são: Codex 38 ready; Copilot 34 ready/4 needs_revision; Claude 37 ready/1 needs_revision. Os desacordos históricos adicionais são `credential-source-cutovers` e `research-dispatch-transport-boundary` no Copilot, e `research-dispatch-transport-boundary` no Claude. As decisões de preservar contexto histórico e referências Finance delimitadas continuam documentadas nos relatórios anteriores. Esses 22 pacotes não foram reavaliados nesta manutenção.

A minha conclusão é que cruzar pareceres com exercícios executáveis melhorou a biblioteca: foram encontradas falhas que coexistiam com avaliações ready. A manutenção deve continuar a exigir evidência, âmbito claro e decisões explícitas sobre desacordos.

À conclusão da validação, os ficheiros estavam locais, ainda sem commit nem push.
