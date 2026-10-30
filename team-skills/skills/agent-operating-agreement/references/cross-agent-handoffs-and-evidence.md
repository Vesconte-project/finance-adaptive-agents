# Handoffs e evidência entre agentes

Lê ao coordenar implementação, observação do host e revisão por pessoas ou agentes
com acessos diferentes. Complementa o acordo adotado; não cria autoridade para
aceitar, fazer merge, operar produção ou delegar trabalho sem autorização.

## Uma mensagem que outro agente consegue executar

Inclui objetivo e decisão pedida, âmbito e exclusões, código revisto e baseline
instalada, observações com data UTC e origem, o que falta provar, autorização já
dada e próximo passo. Distingue:

- **confirmado no alvo**, com data, versão e prova;
- **lido no código**, fixado à versão, sem alegar execução;
- **hipótese**, com a observação mínima que a confirmaria ou recusaria.

Fecha com condição de sucesso, STOP, janela e recuperação aplicáveis. Não dependas
de "como ontem", do histórico do chat nem de o fundador voltar a explicar o caso.
Uma referência a evidência só serve se o destinatário a conseguir ler; quando não
consegue, entrega um resumo sanitizado suficiente e a sua proveniência. Deixa os
originais privados no alvo. Não peças logs ou bases inteiras quando datas,
contagens e códigos permitem decidir. Uma saída grande pode ficar num relatório
sanitizado, com nome único e hash; a consola mostra estado e localização.

O agente de implementação recebe contratos e um pedido de PR; o agente com acesso
ao host recebe perguntas de leitura e critérios de prova; o revisor recebe o
delta concreto, evidência e limitações. Esses papéis são responsabilidades, não
identidades com privilégios implícitos. Uma descoberta do host não autoriza uma
correção manual, e uma sugestão do revisor não equivale a execução pelo operador.

## A prova tem um âmbito

Regista separadamente proposto, revisto, testado, integrado, instalado e verificado
para o objetivo concreto. Usa os estados do workflow existente, sem inventar
etapas obrigatórias para tarefas simples. "Aceite" pode significar pedido em fila
ou aprovação humana: escreve qual. Para o protocolo de resultados de deploy,
consulta `deploy-outcome-visibility`; não cries outro protocolo no handoff.

CI verde prova os checks que correram. Se o workflow já espera e valida o deploy,
usa esse resultado e recibo; não peças uma nova bateria manual por rotina. Uma
verificação funcional adicional só é necessária quando cobre um critério ainda
não observado ou um incidente concreto. Local verde sem CI remoto consultável
continua a ser prova local, não CI verde inferida.

Também distingue sucesso do flow de cobertura dos dados e de disponibilidade do
produto. Uma correção pode recuperar seleção sem reparar dados antigos; mudar um
filtro pode voltar a selecionar dados desatualizados. Reporta universo antes/depois,
exclusões e frescura no ponto de consumo quando essa for a decisão. Os contratos
específicos pertencem às skills de seleção, cobertura e disponibilidade; este
acordo só exige que o handoff não esconda a lacuna entre essas provas.

## Registos duráveis sem duplicar estado

Usa a issue existente no Linear para ação, responsável, dependências, estado e
resultado curto, ligado ao PR e à evidência. Usa a página existente no Notion para
contexto, razões, decisões e interpretação histórica, com ligações à execução.
Confirma a convenção local: esses sistemas não são universalmente fontes de
aceitação. Não copies um diário completo para ambos nem cries uma segunda issue
para a mesma ação. Corrige uma afirmação antiga indicando data e âmbito da
substituição; um comentário novo não torna toda a página atual.

No handoff final, indica o que foi realmente gravado e onde. Prosa nesta conversa
não significa ficheiro criado, PR aberto, issue atualizada ou skill distribuída.
Se a escrita não estava autorizada ou a ferramenta falhou, entrega a proposta e
identifica essa lacuna, sem declarar persistência. Conhecimento reutilizável vai
para a skill canónica; estado operacional e dados privados continuam nas suas
fontes. Não materializes novas versões nos consumidores implicitamente.

## Evidência e limites

Revisão de 30/10/2026 cruzou as notas operacionais de 26–30/10 com o Linear
(ENG-172 e ENG-196) e as páginas Notion “Operações de produção V2 — releases e
mudanças simples, repetíveis e automatizáveis” e “Operações de produção —
contratos técnicos, investigação e evidência”. As páginas já distinguiam fases
instaladas de fases propostas, provas sintéticas de cenários reais não exercitados
e um recálculo concluído de ingestão/retoma ainda pendentes. O apêndice de 18–21/10
registava baselines obsoletas e seis gerações de auxiliares quase iguais. Isso
sustenta transferir contratos e evidência delimitada, não perpetuar scripts por
janela como regra geral.

No caso de 26–30/10, verificadores manuais de deploy já concluído aumentaram o
trabalho do operador; o destino proposto era tornar o resultado automático visível.
A mesma revisão encontrou leituras que só produziram relatórios, enquanto o
trabalho do catálogo continuava por publicar. O acordo deve nomear essa diferença,
não afirmar que documentação ou automação propostas já estão instaladas.

Estes são exemplos de coordenação neste projeto e nestas datas, não prova de que
todas as equipas devam usar os mesmos sistemas nem de que um teste substitua
aceitação humana onde esta for exigida.

## Corrigir a descoberta da skill, sem duplicar o conteúdo

Na revisão do catálogo de 30/10/2026, três descrições deixavam casos observados fora
do seu gatilho: `agent-operating-agreement` só era descoberto perante pedido
explícito de acordo, mesmo num handoff que já o seguia; a skill de releases
imutáveis só descrevia a transição de checkouts, omitindo retenção posterior; a
skill de provas de integração não nomeava o dryrun autorizado no alvo real.
O complemento alarga essas descrições e liga referências específicas, mantendo
as fronteiras de autorização. É correção de descoberta, não um novo workflow.

O padrão "aceite ainda não é concluído" já estava em `deploy-outcome-visibility`
e `orchestrator-runtime-ops`. As exclusões de seleção e os sinais de fornecedor
estavam no âmbito das novas skills propostas pelo PR #9 deste catálogo. A decisão
é reutilizar esses donos, não criar variantes com nomes diferentes. Confirma a
versão do catálogo disponível: uma referência a trabalho proposto não demonstra
que ele já foi integrado ou distribuído aos outros repositórios.
