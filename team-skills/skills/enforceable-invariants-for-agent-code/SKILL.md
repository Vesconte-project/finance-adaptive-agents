---
name: enforceable-invariants-for-agent-code
description: Tornar obrigatória uma regra transversal de segurança ou arquitetura (limites de pedidos, autenticação, autorização, segredos, remoção sem compatibilidade) num repositório onde agentes de código escrevem e revêem alterações, ligando um documento curto de invariantes a testes que falham o CI. Usa ao criar uma regra destas, ao rever código que a contorna, ou quando um revisor repete o mesmo comentário. Não para estilo que um linter já cobre nem para uma correção pontual sem padrão.
---

# Uma regra que só está escrita será contornada

Cada agente começa sem memória. Pode não ler a documentação, ou ler e concluir
que o seu caso é exceção, com um argumento plausível. Um caso real: uma família
nova de rotas internas ficou de fora do limite por IP do middleware, com uma
condição `and not <rota_nova>`, "porque já tinha limite por identidade". O
limite por identidade só atuava depois de o token ser aceite, e cada token
falso com formato válido abria uma transação na base. O código passou nos
testes, porque nenhum teste verificava a regra.

A decisão que esta Skill muda: **uma regra transversal só fica garantida pelo CI se
uma verificação executada nesse CI falhar quando ela é violada.** A
documentação explica o porquê; o teste impede a repetição.

## O padrão

1. **Documento de invariantes, curto.** Um ficheiro por repositório (por
   exemplo `docs/SECURITY-INVARIANTS.md`). Cada regra tem uma frase
   verificável, o porquê numa linha e o nome do teste que a garante. Uma regra
   sem teste fica marcada como tal, para não parecer garantida.
2. **Ponteiro no ponto de entrada dos agentes.** Uma linha no `AGENTS.md` (ou
   equivalente) a dizer quando ler o documento: antes de mexer em rotas,
   autenticação, middleware ou segredos. Não copies as regras para lá.
3. **Teste de inventário.** O teste enumera a superfície real a partir do
   registo em runtime (as rotas da aplicação instanciada, os jobs registados,
   as roles da base), não por grep ao código. Assim, uma rota nova fica
   coberta sem ninguém se lembrar dela.
4. **Exceções como dados.** Uma lista explícita e curta, com a razão de cada
   exceção, revista no PR como qualquer código. Uma exceção nova é uma
   alteração visível, não uma condição escondida num `if`.
5. **Mensagem de erro que ensina.** Quando o teste falha, diz que regra foi
   violada, onde está o documento e como adicionar uma exceção legítima.

## Testa a propriedade, não a implementação

Verifica o comportamento que a regra protege. Por exemplo, para limites de
pedidos: N pedidos com credenciais falsas mas de formato válido recebem 429
antes de qualquer acesso à base; um pedido legítimo continua a passar dentro
do limite. Um teste que só confirma que certa função foi chamada deixa passar
uma implementação nova que a contorna.

Inclui pelo menos um caso negativo que introduza uma violação controlada e
prove que o guarda falha; evita que uma superfície vazia seja aceite como prova.

## Evidência de camadas externas

Regras em edge/CDN, painéis de fornecedores ou gateways geridos podem ter
configuração versionada, revisão e verificações automatizadas. Procura primeiro
evidência no repositório (IaC, políticas, testes) e, se já houver acesso e
autorização para o alvo, evidência do estado aplicado. Configuração pretendida
e estado instalado são provas diferentes; sem esse acesso, usa evidência
sanitizada disponível e regista o que não foi confirmado.

Se uma regra externa for essencial, regista a dependência, o ponto onde é
aplicada e a evidência que a cobre. Distingue "verificado pelo CI", "verificado
fora do CI" (com origem/data) e "não verificado". Não concluas que a proteção
dentro do serviço é redundante apenas por existir outra camada: demonstra que
as garantias e caminhos de acesso relevantes ficam cobertos antes de propor
a remoção.

## Sinais de alarme

- Uma regra que só aparece em revisões ou em documentação.
- O mesmo comentário de revisão em PRs de agentes diferentes.
- Condições de exclusão como `and not X` em middleware de segurança.
- Uma exceção sem razão escrita, ou "temporária" sem data nem issue.
- Um teste de inventário construído a partir de uma lista estática de
  caminhos, que não apanha código novo.

## Quando não aplicar

Num script de uso único e baixo impacto, uma checklist de revisão pode ser
suficiente. Escolhe inventário e testes quando houver uma superfície útil a
cobrir e risco de violação recorrente com impacto de segurança ou dados.
Vários autores ou agentes podem aumentar esse risco; um único autor também
pode beneficiar destas garantias. Não forces um inventário sem relação com a
propriedade que se quer proteger.

## Relacionadas (leitura opcional, se disponíveis)

- `guards-that-pass-blindly`: um guarda que não vê passa sempre.
- `clerk-fastapi-trust-boundaries`: fronteiras de identidade que estas regras
  costumam proteger.
