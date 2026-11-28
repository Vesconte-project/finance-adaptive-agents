---
name: agent-authority-broker
description: Desenhar, implementar ou rever o controlo do que agentes de IA podem fazer (mandatos, permissões por operação, aprovações humanas, credenciais) numa plataforma de agentes com contentores, quando é preciso distinguir uma garantia imposta de uma cooperativa. Não para permissões de utilizadores humanos numa aplicação nem para escolher um fornecedor de modelos.
---

# Autoridade de agentes: um broker sem modelo, não um prompt

A pergunta que esta Skill muda: "um agente com instruções injetadas consegue fazer isto?". A
resposta só é "não" quando o agente não chega à credencial nem ao efeito por outro caminho. Um
prompt, um perfil ou um botão de aprovação não são fronteiras.

**Evidência.** Desenho e implementação em oito fases numa plataforma de agentes local
(Paperclip, PostgreSQL, Docker no WSL), 2026-11, com cinco hipóteses de segurança testadas.
Ver [references/achados-2026-11.md](references/achados-2026-11.md).

## Princípios

1. **Um broker sem modelo fica com as credenciais e executa.** O agente pede; nunca recebe a
   credencial nem um "sim" reutilizável. Cada capacidade tem um ponto de aplicação declarado
   (montagem, rede, ferramenta do broker, executor). Capacidade sem ponto de aplicação é
   recusada; capacidade sem ferramenta (merge, produção, pagamentos) é `never` por ausência de
   caminho, além da regra.
2. **Identidade do chamador nunca vem do agente.** Numa arquitetura com lançador no host (a que
   foi provada), o lançador pede ao broker um
   token por execução ligado a espaço, agente, perfil@versão, modelo, tarefa, repositório e
   validade; guarda-se só o hash. Revogar os tokens no arranque do broker.
3. **Decisão efetiva = o mais restritivo** entre perfil (teto versionado em Git), mandato
   assinado e âmbito da atribuição. Sem regra, recusa. `never` ganha sempre. Um mandato aperta,
   nunca alarga.
4. **A ação é canónica e com digest.** JSON ordenado e SHA-256. O broker guarda o conteúdo
   exato (bundle Git, corpo da mensagem) e executa a partir dessa cópia; depois da aprovação,
   o agente não volta a fornecer parâmetros.
5. **Aprovação humana = assinatura sobre o digest**, com validade, epoch e namespace próprios,
   consumida uma vez (chave primária na tabela de consumos). O texto que o humano revê é gerado
   da própria declaração, nunca da descrição do agente. O botão "Aprovar" da plataforma é um
   espelho: não autoriza nada; "Rejeitar" pode cancelar, porque só restringe.
6. **Revalidar na execução.** Mandato relido com bloqueio dentro da transação que passa a
   operação a `executing`. Uma revogação entre decisão e execução tem de ganhar.
7. **Epoch fora da base** (uma opção; o requisito é que um restauro não reative aprovações).
   Restaurar uma cópia antiga "desconsome" aprovações. Incrementa o
   epoch depois de restaurar ou migrar; tudo o que estava pendente expira.
8. **Falha fecha.** Broker ou base parados: `unavailable`, sem cache de permissões. Execução
   sem recibo passa a `unknown` e reconcilia-se lendo o fornecedor; nunca repetir às cegas.

## Separa "imposto" de "cooperativo"

Antes de chamar a uma garantia "imposta", verifica no ambiente real, com as sondas ativas só sob autorização explícita (ver o checklist em
[references/verificacoes.md](references/verificacoes.md)):

- Agentes no host com o mesmo UID dos segredos, ou no grupo `docker`, são só **cooperativos**:
  o grupo `docker` equivale a root. Diz isso nos recibos (`enforcement: cooperative`).
- A credencial de subscrição montada num contentor pode trazer tokens OAuth de outros serviços.
  Monta um ficheiro derivado mínimo, gerado no host com modo 0600.
- A conta de máquina que publica PRs pode também fazer merge se as regras do ramo não o
  impedirem. Confirma; é a primeira coisa a fechar.
- Workflows de CI podem expor segredos a PRs de ramos internos: um push do agente corre código
  com esses segredos. Alterações à definição da CI (no GitHub, `.github/**`) passam a exigir aprovação.
- A chave de assinatura do humano não pode estar ao alcance dos agentes (não reutilizar a chave
  SSH pessoal); preferir FIDO com presença física. Sem chave dedicada configurada, as operações
  que pedem aprovação ficam em espera com um erro claro.

## Ordem de implementação que funcionou

Recomendação a partir de um caso, não sequência obrigatória.

1. Núcleo puro `evaluate()` com tabela de decisão sobre os perfis reais.
2. Esquema SQL com papéis separados (dono, broker só por funções, leitor); concorrência com um
   só vencedor testada num PostgreSQL real na CI.
3. Broker com token por execução; só leituras; escritas em modo sombra (avaliadas e
   registadas, nunca executadas).
4. Primeira escrita real: publicação de um ramo a partir de um bundle validado (repositório,
   prefixo do ramo, base esperada, caminhos, tamanho), sem correr hooks nem código do bundle no
   host; recibo com o SHA remoto verificado.
5. Aprovações assinadas. 6. Fechar a passagem direta (gateway só para o broker, lista de rotas,
   credenciais mínimas, testes de fuga). 7. Outras escritas. 8. Migração com epoch.

Cada fase entrega algo verificável e não alarga a confiança antes de a anterior estar provada.

## Quando não aplicar

Permissões de utilizadores humanos numa aplicação; agentes sem efeitos externos; escolha de
modelos. Esta Skill não concede acesso nem substitui as regras do fornecedor (proteção de
ramos, âmbito dos tokens).
