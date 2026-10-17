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

A decisão que esta Skill muda: **uma regra transversal só existe se um teste
falhar quando ela é violada.** A documentação explica o porquê; o teste
impede a repetição.

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

Inclui pelo menos um caso negativo que prove que o guarda consegue falhar
(ver `guards-that-pass-blindly`).

## Camadas que o agente não vê

Regras aplicadas fora do repositório (edge/CDN, painéis de fornecedores,
gateways geridos) não estão no git, não têm revisão e nenhum agente as consegue
verificar ao escrever código. Não as uses como justificação para remover uma
proteção dentro do serviço: cada camada protege contra falhas diferentes e
pode mudar sem aviso. Se uma regra externa for essencial, regista-a como
dependência no documento de invariantes, com o estado "não verificado pelo
CI".

## Sinais de alarme

- Uma regra que só aparece em revisões ou em documentação.
- O mesmo comentário de revisão em PRs de agentes diferentes.
- Condições de exclusão como `and not X` em middleware de segurança.
- Uma exceção sem razão escrita, ou "temporária" sem data nem issue.
- Um teste de inventário construído a partir de uma lista estática de
  caminhos, que não apanha código novo.

## Quando não aplicar

Num script de uso único, num repositório com um só autor humano e sem agentes,
ou numa regra sem superfície enumerável, isto é excesso: chega uma checklist
de revisão. O custo justifica-se quando há vários autores, sobretudo agentes,
e a violação tem impacto de segurança ou de dados.

## Relacionadas

- `guards-that-pass-blindly`: um guarda que não vê passa sempre.
- `clerk-fastapi-trust-boundaries`: fronteiras de identidade que estas regras
  costumam proteger.
