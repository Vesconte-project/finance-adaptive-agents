---
name: overnight-agent-orchestration
description: Coordenar vários agentes de implementação sem o dono presente (por exemplo durante a noite), quando o coordenador delega unidades de trabalho, revê e faz merge dentro de uma autorização explícita, gere contas de modelo que esgotam e deixa um relatório para a manhã. Não para uma tarefa única feita pelo próprio agente nem para decidir autorizações que o dono não deu.
---

# Orquestrar agentes de implementação na ausência do dono

O coordenador não implementa: transforma um plano em unidades pequenas, escreve pedidos que
um agente sem histórico consegue cumprir, verifica o que volta e mantém o trabalho a andar
quando contas, serviços ou agentes falham. O objetivo é que o dono acorde com trabalho
integrado, decisões registadas e uma lista curta do que só ele pode fazer.

**Evidência.** Uma noite de coordenação (2026-11) com agentes Codex e Claude delegados por um
orquestrador local: 13 PRs integrados num repositório de governança e 11 em repositórios de
produto, duas contas esgotadas e vários agentes mortos a meio. Ver
[references/casos-2026-11.md](references/casos-2026-11.md).

## 1. Fixa a autorização antes de começar

Escreve, num registo durável que sobreviva à compactação do contexto (memória persistente do
agente, página ou issue do projeto, o que o ambiente tiver), exatamente o que o dono delegou: âmbito (que sistemas), o que pode ser decidido sem ele, a regra de merge (por exemplo
"merge com CI verde"; "PRs só de documentação sem esperar pela CI"), a ordem das contas de
modelo e o que continua proibido (produção, credenciais, dinheiro, trabalho de outros agentes).
Autorização dada numa frase solta perde-se na compactação do contexto; escrita, sobrevive.

Quando o dono diz "decide tu" para um âmbito, decide e regista a razão. Quando os critérios que
ele fixou não são todos cumpridos, não decides: preparas opções com recomendação e passas a
outro trabalho. **Nunca pares todo o trabalho por um único bloqueio.**

**Condições de paragem.**

- Sem âmbito delegado explicitamente (que sistemas e repositórios), não lances agentes nem
  publiques ramos ou PRs. Regista a lacuna e prepara um plano ou opções para o dono.
- Com âmbito autorizado mas sem regra de merge ou sem ordem de contas, podes delegar e
  preparar PRs, mas não fazes merge, não usas contas que o dono não listou e não decides por
  ele. Regista a lacuna no relatório.

## 2. Corta o plano em unidades com dependências explícitas

- Uma unidade = um PR pequeno com critério de conclusão verificável.
- Sequencial quando uma unidade usa o que a anterior cria (esquema antes do serviço que o usa).
- Paralelo só com áreas de ficheiros disjuntas. Diz a cada agente que o outro existe, que
  ficheiros evitar e que faça merge do `main` antes de publicar.
- Um único agente de cada vez usa um serviço local partilhado com estado (uma pilha que se
  liga e desliga). Os outros não lhe tocam.
- Verificações sem código (hipóteses de segurança, leitura de configuração) correm em paralelo
  com a implementação e alimentam os pedidos seguintes.

## 3. Escreve pedidos autossuficientes

O agente delegado não tem o teu histórico. Cada pedido inclui, por esta ordem:

1. Instruções a ler primeiro (acordo do ambiente de trabalho, se existir, e as do repositório)
   e páginas de desenho com as secções relevantes.
2. Estado atual já integrado: números de PR e SHAs de merge. Sem isto o agente refaz ou
   contradiz trabalho feito.
3. Âmbito numerado, testes exigidos e o que fica de fora.
4. Regras de coordenação do ambiente. Se houver registo de reservas, checkouts geridos ou
   handoffs, diz qual a chave da unidade e os comandos. Se não houver, pede pelo menos um ramo
   próprio por agente, nada de push para `main`, uma espera pela CI, no máximo duas rondas de
   correção e um relatório final com o estado.
5. Limites: "não fazer merge", nunca imprimir segredos, sem mudanças de credenciais,
   produção ou gastos, não tocar em sessões de outros agentes.
6. Achados de verificações anteriores que o afetam, marcados como "não corrigir aqui salvo se
   trivial; listar como seguimento".
7. Fecho: que linha acrescentar ao registo do projeto e a última linha fixa
   (`PR <url>, head <sha>, checks <state>`), que torna a verificação mecânica.

## 4. Verifica o que volta; não aceites o resumo

Para cada PR entregue:

1. Confirma a CI no SHA exato com uma ferramenta que leia o estado real (não a descrição do
   agente).
2. Lista os ficheiros alterados. Lê o diff de tudo o que é sensível: workflows de CI (segredos,
   gatilhos privilegiados, permissões), funções SQL com privilégios do dono, verificação de
   assinaturas, configurações de rede e montagens.
3. Só se a regra de merge registada no passo 1 o permitir, faz merge. Caso contrário, deixa o
   PR pronto e lista-o no relatório. Se a regra dispensa a CI para PRs só de documentação,
   confirma que nenhum ficheiro é workflow, configuração ou script antes de usar essa exceção.
4. Faz merge fixando o SHA que verificaste (por exemplo `expectedHeadSha`, ou o equivalente da
   tua ferramenta), para não integrar um push posterior não visto.
5. Se o agente morreu depois de abrir o PR, faz tu a verificação e aplica a mesma regra de
   merge. Regista o que ele não chegou a registar ou passa-o ao agente seguinte.

Uma afirmação como "a suite local tem 3 falhas iguais à base" é para confirmar ou anotar, não
para ignorar.

Antes de lançar uma unidade que escolhe uma ferramenta, um fornecedor ou um desenho difícil de
desfazer, aplica a Skill `prior-art-before-design` (ou faz tu essa pesquisa e passa o resultado
no pedido). A primeira proposta de um agente que raciocina do zero muda muitas vezes depois de
ver o que os outros já fazem.

## 5. Contas de modelo que esgotam

- Segue a ordem de contas que o dono definiu; muda para a seguinte só com um sinal de
  esgotamento (limite de uso, créditos esgotados) e regista a hora. Os textos exatos variam
  por fornecedor; os observados estão nos casos.
- Uma ligação ao fornecedor que fecha logo no arranque pode ser transitória: confirma que o
  agente não reservou nada nem escreveu, e relança uma vez na mesma conta antes de descer.
  Isto vem de um só caso; se repetir, trata como indisponível.
- Quando o dono indica para onde vai o trabalho novo ("volta a usar a conta X"), o trabalho
  quase terminado noutra conta pode acabar lá; diz-lho. Se ele pediu para parar ou cancelar o
  uso dessa conta, ou a instrução é ambígua quanto ao que já está a correr, para ou pergunta:
  não continues a gastar nessa conta por defeito.
- Partilhar a conta do coordenador com os agentes reduz o teu próprio orçamento: lança menos.
- Contas que voltam a ter créditos podem esgotar de novo a meio: um pedido bem escrito deixa
  o trabalho recuperável (PR aberto cedo, registo no fim de cada fase).

## 5.1 Pedidos vindos de outro agente

Alguns agentes recusam começar quando o pedido não vem diretamente do dono, mesmo com a
autorização citada e o registo indicado. Quando o ambiente for assim, avisa o dono ao lançar
(«confirma no fio do agente»), ou usa uma conta que o dono autorizou e que não exige essa
confirmação. Não tentes contornar a recusa com texto mais insistente.

## 5.2 Plataforma temporária

Se o dono diz que a máquina é temporária, não instales nem extraias software em locais
avulsos. Usa imagens de contentor e o repositório, documenta o que fica no host (caminhos,
imagens, unidades, retenção de cópias) e como desinstalar sem perder cópias.

## 6. Agentes mortos e reservas presas

Se o ambiente regista reservas ou checkouts por agente, uma reserva cuja sessão morreu continua
reservada. Não a adoptes nem apagues o checkout sem o procedimento de recuperação do ambiente.
Relança com uma identidade nova (por exemplo `…/r2`) e diz ao novo agente que não toque na
antiga. Se o agente morto deixou trabalho por gravar, o novo pode lê-lo (diff e ficheiros, só
leitura), rever e portar o que estiver bem para o seu próprio checkout. Sem registo, usa pelo menos um ramo novo e não reutilizes o diretório do agente morto.
Lista o que ficou preso no relatório para o dono.

## 7. Relatório para o dono

Mantém atualizado, no registo do projeto, um resumo no topo e um diário por entrada. Quando o
dono pergunta o estado, responde em quatro partes: o que se fez (com PRs e SHAs), o que está a
correr (com ligações), o que decidiste e porquê, e o que precisa dele, ordenado por urgência.
Separa "integrado", "instalado localmente" e "provado de ponta a ponta": não são a mesma coisa.

## Ferramentas que falham de forma previsível

Ver [references/ferramentas.md](references/ferramentas.md) para respostas grandes de MCP
gravadas em ficheiro, 403 em check-runs, atualizações de páginas que exigem texto exato e
outros contornos verificados.

## Quando não aplicar

Uma tarefa que o próprio agente faz de uma vez; trabalho em que o dono está presente para cada
decisão; qualquer passo de produção, credenciais ou dinheiro, que esta Skill não autoriza.
