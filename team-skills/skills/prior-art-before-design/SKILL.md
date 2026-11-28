---
name: prior-art-before-design
description: Antes de recomendar uma escolha de desenho, arquitetura, ferramenta ou fornecedor difícil de desfazer, pesquisar como outros já resolvem o mesmo problema, comparar pelo menos duas alternativas (incluindo adotar uma solução existente) e confrontá-las com as restrições do dono. Não para passos pequenos e reversíveis, nem para tarefas cujo enunciado já fixa a solução.
---

# Ver o que já existe antes de propor

A decisão que esta Skill muda: **a primeira ideia não é a recomendação.** Um agente que
raciocina do zero produz propostas plausíveis que mudam assim que alguém pergunta «e os
outros, como fazem?». Quase sempre o problema já foi pensado. Se há uma solução provada,
adota-a e adapta-a; reinventar custa tempo e acrescenta defeitos.

Esta Skill informa a preparação de uma recomendação. Não concede autorização para instalar,
contratar, gastar nem criar contas; essas decisões continuam com quem as tem.

**Evidência.** Um dia de coordenação de uma plataforma de agentes (2026-11): quatro
recomendações do coordenador mudaram depois de pesquisa ou de uma pergunta do dono. Ver
[references/casos-2026-11.md](references/casos-2026-11.md).

## Quando aplicar

- Escolha de ferramenta, fornecedor, produto, protocolo ou padrão de arquitetura.
- Desenho de segurança, autorização, custódia de segredos ou aprovação humana, quando a
  escolha for difícil de desfazer.
- Qualquer decisão que custe caro desfazer: dados migrados, contratos, contas criadas,
  hábitos do dono.

Não aplicar a passos pequenos e reversíveis (renomear, um teste, uma correção local): aí,
age. Pesquisar tudo também é uma forma de não avançar.

## Procedimento

1. **Formula o problema sem a tua solução.** «Aprovar ações de agentes de forma que nenhum
   agente forje a aprovação», não «configurar uma chave FIDO».
2. **Procura o estado da arte**, se tiveres ferramentas de pesquisa e estiveres autorizado a
   usá-las: normas e rascunhos (IETF, W3C, OpenID), documentação de fornecedores do domínio,
   projetos open source, padrões validados publicados por empresas de referência,
   discussões técnicas recentes. Regista as fontes que consultaste. Descreve o problema de
   forma genérica nas pesquisas, sem nomes, hosts, segredos ou detalhes privados do dono.
   **Sem pesquisa disponível:** lista as alternativas a partir do teu conhecimento e diz que
   é isso que estás a fazer; marca como não verificados preços, limites de planos, versões
   e o quão atual é cada informação; diz o que o dono (ou uma sessão com acesso) deve
   confirmar antes de decidir. Nunca apresentes como fonte uma página que não abriste, nem
   como «confirmado» um limite que não verificaste.
3. **Põe na mesa pelo menos duas alternativas, sendo uma «adotar o que já existe».** Inclui
   também a opção mínima (não fazer, ou usar o que o dono já tem).
4. **Confronta com as restrições do dono**, ditas ou registadas: custo (há plano gratuito?),
   manutenção (quem opera isto daqui a seis meses?), portabilidade (a máquina é temporária?),
   ferramentas que já usa, região e dados pessoais.
5. **Desconfia das fontes.** Comparações escritas pelo próprio fornecedor favorecem-no;
   procura pelo menos uma fonte independente ou a documentação oficial do concorrente.
   Confirma limites de planos gratuitos na página do fornecedor quando a puderes consultar;
   caso contrário, marca-os como por confirmar.
6. **Escreve a recomendação com o que a faria mudar.** «Recomendo X; se Y for verdade,
   passo a Z.» Se não consegues dizer o que mudaria a decisão, ainda não a pensaste.
7. **Adaptar não é copiar às cegas.** Verifica onde a solução existente assume algo que no
   teu caso é falso (por exemplo, um modelo de IA no caminho de uma aprovação) e diz a
   adaptação.

## Sinais de que saltaste este passo

- A proposta tem uma só opção.
- O dono pergunta «porquê esta e não aquela?» e a resposta exige pesquisar agora.
- Disseste «não existe» ou «não está instalado» sem procurar.
- A solução exige manter um serviço próprio quando há um alojado equivalente, ou comprar
  algo quando há um padrão gratuito.

## Quando não aplicar

Passos reversíveis e locais; tarefas em que o enunciado já fixa a solução; emergências em
que a mitigação imediata vem antes da escolha definitiva (regista a escolha para depois).
