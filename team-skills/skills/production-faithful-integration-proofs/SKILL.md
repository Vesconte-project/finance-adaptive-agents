---
name: production-faithful-integration-proofs
description: Desenhar ou interpretar provas de integração descartáveis, dryruns de leitura autorizados ou testes de helpers operacionais quando o resultado decide uma alteração real em produção. Usa para avaliar se topologia, autenticação, permissões, estado, formas de dados e contratos produtor–consumidor sustentam a conclusão. Não para testes unitários de lógica pura nem provas sem consequência em produção.
---

# Uma prova só vale nas dimensões que reproduz

As instruções orientam a prova; não concedem autorização para aceder ao alvo, alterar dados, instalar ou publicar.

Uma prova descartável é evidência sobre o ambiente que montou. Se a topologia,
a autenticação ou o estado diferirem de produção, a prova pode **falhar por
uma razão que não existe em produção** ou **passar por uma razão que não se
aplica lá**. As duas levam a decisões erradas: abandonar uma versão que
funcionava, ou instalar uma que vai falhar.

Num caso operacional relatado, um pooler de ligações parecia não autenticar
com o pool frio numa versão nova, e chegou a discutir-se construir uma imagem
própria. Em produção, o pooler partilhava o namespace de rede da base e chegava
por loopback, onde as regras de acesso eram diferentes; a prova punha-os em
redes separadas. Segundo a evidência fornecida, com a topologia de produção
reproduzida, a mesma versão passou. O problema estava na prova.

## Dryrun autorizado contra o alvo real

Para comparar um loader de PR com o instalado usando apenas leitura autorizada,
lê [references/pinned-read-only-pr-probes.md](references/pinned-read-only-pr-probes.md).
Fixa código e SELECT, usa a identidade real e declara os limites da prova;
extração por AST não é sandbox e uma transação READ ONLY não contém código hostil.

## Evidência que se perde entre componentes

Numa prova abrangida pelo âmbito desta Skill, quando uma normalização, descarte,
relatório ou resolução de identidade pode mudar uma decisão de validação ou autorização,
lê [references/evidence-through-transformations.md](references/evidence-through-transformations.md).
Mapeia a observação até à decisão e liga a saída real do produtor ao consumidor real:
um teste isolado de rejeição não prova que essa rejeição chegou ao gate final.

## Antes de concluir, confirma as dimensões

Se a decisão depende de um instalador empacotado ou de um consumidor com outra
identidade, lê [references/artifact-roundtrip-and-consumer-identity.md](references/artifact-roundtrip-and-consumer-identity.md).
O checkout e uma leitura como root não provam o pacote extraído nem o acesso do
serviço. Para leitores Python privilegiados e URLs PostgreSQL construídos pela
sonda, lê [references/privileged-python-and-libpq-probes.md](references/privileged-python-and-libpq-probes.md).

Para cada uma, pergunta se a prova reproduz produção ou se a diferença é
irrelevante para a decisão:

- **Topologia de rede:** namespaces partilhados ou separados, loopback vs.
  rede, o endereço de cliente que o servidor realmente vê.
- **Cadeia de autenticação:** em cada salto, o método efetivo (regras de
  acesso por ordem, trust local, SCRAM vs. MD5, passthrough), não o método que
  se presume.
- **Estado existente:** formato das credenciais já criadas, ficheiros mistos
  (entradas antigas e novas), versões de schema de partida, permissões já
  concedidas.
- **Forma dos dados:** dados sintéticos com as formas relevantes que o código
  vai encontrar, incluindo histórico suficiente e combinações adversariais.
  Nunca dados reais de utilizadores.
- **Versões e identidades:** versão/digest real, entrypoint, UID/GID, roles e
  privilégios efetivos em cada salto. Não pressuponhas root nem non-root;
  reproduz as propriedades relevantes num ambiente de prova autorizado, sem
  copiar credenciais reais nem conceder privilégios fora desse âmbito.

## Método

1. **Obtém a descrição de produção.** Quando o acesso ao alvo já estiver
   autorizado e as ferramentas estiverem disponíveis, recolhe só os metadados
   necessários, em leitura e sem segredos: ligações, regras de acesso e
   formatos. A capacidade de ler não concede autorização. Sem esse acesso, usa
   descrições sanitizadas fornecidas pelo utilizador ou evidência existente;
   explicita as dimensões não verificadas e limita a conclusão.
2. **Guarda a descrição sanitizada** junto da prova apenas se houver destino
   apropriado e escrita autorizada no projeto; trata divergências como
   alterações revistas. Caso contrário, apresenta-a como resultado da análise
   com a sua origem e limitações, sem criar ficheiros no projeto.
3. **Faz a prova afirmar a topologia**, não só o resultado: verifica, por
   exemplo, que o endereço de cliente visto pelo servidor é o esperado. Uma
   prova que reproduz a topologia por acaso deixa de a reproduzir em silêncio.
4. **Compara valores normalizados.** Endereços, tipos e formatos podem vir
   representados de forma diferente (por exemplo um endereço com e sem `/32`);
   normaliza antes de comparar, em vez de afrouxar a verificação.

## Testes de helpers operacionais com simulações

Um helper escrito para uma janela de produção costuma ser testado com o sistema,
a base e o HTTP simulados. Esses testes provam a lógica do helper, não os
contratos com o que está instalado. A evidência operacional fornecida relata
helpers com testes verdes que falharam por expectativas escritas à mão:

- um campo lido de um checkpoint que a função publicada não devolvia
  (o teste usava um dicionário inventado com esse campo);
- um ficheiro de credenciais do pooler tratado como `root:root 0600` quando era
  `root:<grupo-do-pooler> 0640` (os testes simulavam a verificação de
  permissões como identidade);
- uma sonda com um parâmetro de arranque que o pooler recusava (a ligação era
  simulada);
- uma contagem fixa de verificações que mudara com um consumidor novo;
- `404` esperado em rotas retiradas com uma credencial de serviço a que o
  servidor respondia corretamente `403` naquele contrato.

Verificações dirigidas a essas falhas:

- **Formas reais:** gera as estruturas de entrada com as funções publicadas
  ou com amostras autorizadas e sanitizadas só de metadados, em vez de
  dicionários feitos à mão.
- **Inventário de ficheiros:** usa dono, grupo e modo confirmados no alvo
  apenas com autorização e acesso já concedidos, em leitura. Sem esse acesso,
  usa evidência sanitizada disponível e declara o inventário por confirmar.
  Leva essas propriedades aos testes, incluindo o restauro, que não pode impor
  `0600` a um ficheiro que um serviço precisa de ler.
- **Contagens e listas derivadas** da configuração instalada, com comparação
  do conjunto exato, em vez de constantes escritas à mão.
- **Contratos de protocolo** (respostas HTTP, parâmetros aceites por um pooler)
  tirados dos testes ou da configuração do componente responsável na revisão
  fixada, ou provados contra o componente real com essa configuração.
- **Ponta a ponta por ação:** cada ação do CLI tem pelo menos um teste que a
  corre inteira com as fronteiras simuladas, não só as funções intermédias.
- **Simuladores estritos:** um `systemctl`, `psql` ou CLI simulado deve refletir
  as opções e os formatos da interface instalada. Foi relatada uma divergência
  em que o simulador aceitou `systemctl --utc show` e o CLI real recusou a
  invocação. Isso não estabelece uma regra universal por versão; verifica a
  interface efetiva antes de codificar a expectativa no simulador.
- **Volume proporcional:** provas de memória e de tempo usam volumes da ordem
  dos relevantes em produção, incluindo o histórico necessário. Foi relatado
  um builder que carregava o histórico inteiro, passava com amostras pequenas
  e excedeu o limite de memória na execução real.
- **Conteúdo esperado do commit instalado:** quando um helper fixa os ficheiros
  esperados de uma release, tira-os da árvore do merge realmente instalado,
  nunca da cabeça de um PR. Dois PRs com a mesma base não se incluem um ao outro.

Quando um destes testes passa, a conclusão é "a lógica está certa para as
formas que o teste usou". Diz quais formas foram reais e quais foram assumidas.
Os relatos acima motivam as verificações; este pacote não inclui uma suite
independentemente executável que os reproduza.

## Sinais de que a prova está a mentir

- Uma falha que não corresponde a nenhum sintoma observado em produção.
- Uma correção que só mexe no ambiente da prova e "resolve".
- Uma conclusão forte ("a versão X está partida") tirada de uma única
  topologia que ninguém comparou com produção.
- Dados sintéticos que nunca exercitam o caminho que vai correr em produção.
- Testes verdes de um helper cujas entradas, permissões ou respostas foram
  todas escritas pelo próprio autor do helper.

Estes sinais justificam investigar a fidelidade da prova; isoladamente, não
estabelecem que o código ou a prova estejam errados.

## Quando não aplicar

Se a decisão depender apenas de lógica pura, parsing ou cálculos, usa testes
unitários adequados. Uma divergência entre produtor e consumidor pode exigir
uma prova dessa fronteira sem reproduzir toda a infraestrutura. O custo de
reproduzir dimensões de produção justifica-se quando elas condicionam a decisão
sobre uma alteração real.

## Relacionadas (leitura opcional, se disponíveis)

- `verify-against-the-host`: confrontar uma proposta com o estado instalado.
- `stateful-service-migrations`: quando o estado de partida faz parte do risco.
