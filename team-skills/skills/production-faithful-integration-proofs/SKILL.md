---
name: production-faithful-integration-proofs
description: Desenhar ou interpretar uma prova de integração descartável (CI, contentores, base efémera), ou os testes de um helper operacional que vai correr em produção, quando o resultado vai decidir uma alteração real como um pool de ligações, autenticação entre serviços, rede, permissões, migrações ou um corte. Usa quando uma prova destas falha ou passa e é preciso saber se a conclusão vale para produção. Não para testes unitários de lógica pura nem para provas sem consequência em produção.
---

# Uma prova só vale nas dimensões que reproduz

Uma prova descartável é evidência sobre o ambiente que montou. Se a topologia,
a autenticação ou o estado diferirem de produção, a prova pode **falhar por
uma razão que não existe em produção** ou **passar por uma razão que não se
aplica lá**. As duas levam a decisões erradas: abandonar uma versão que
funcionava, ou instalar uma que vai falhar.

Caso real: um pooler de ligações parecia não autenticar com o pool frio numa
versão nova, e chegou a discutir-se construir uma imagem própria. Em produção,
o pooler partilhava o namespace de rede da base e chegava por loopback, onde
as regras de acesso eram diferentes; a prova punha-os em redes separadas. Com a
topologia de produção reproduzida, a mesma versão passou. O problema era da
prova.

## Antes de concluir, confirma as dimensões

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
- **Forma dos dados:** dados sintéticos com a mesma forma que o código vai
  encontrar (histórico suficiente, todas as combinações que produção tem).
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
contratos com o que está instalado. Numa mesma noite (20/10/2026), helpers com
dezenas de testes verdes falharam cinco vezes em produção, sempre por uma
expectativa escrita à mão:

- um campo lido de um checkpoint que a função publicada não devolve
  (o teste usava um dicionário inventado com esse campo);
- um ficheiro de credenciais do pooler tratado como `root:root 0600` quando era
  `root:<grupo-do-pooler> 0640` (os testes simulavam a verificação de
  permissões como identidade);
- uma sonda com um parâmetro de arranque que o pooler recusa (a ligação era
  simulada);
- uma contagem fixa de verificações que mudara nesse dia com um consumidor novo;
- `404` esperado em rotas retiradas com uma credencial de serviço a que o
  servidor responde `403`, que é o comportamento correto.

Regras que teriam apanhado os cinco:

- **Formas reais:** gera as estruturas de entrada com as funções publicadas
  (ou de amostras reais só com metadados), em vez de dicionários feitos à mão.
- **Inventário de ficheiros:** dono, grupo e modo dos ficheiros que o helper
  verifica ou restaura vêm de um inventário confirmado no alvo e são usados nos
  testes, incluindo o restauro (que não pode impor `0600` a um ficheiro que um
  serviço precisa de ler).
- **Contagens e listas derivadas** da configuração instalada, com comparação
  do conjunto exato, nunca de constantes.
- **Contratos de protocolo** (respostas HTTP, parâmetros aceites por um pooler)
  tirados dos testes ou da configuração do dono no SHA fixado, ou provados contra
  o componente real com essa configuração.
- **Ponta a ponta por ação:** cada ação do CLI tem pelo menos um teste que a
  corre inteira com as fronteiras simuladas, não só as funções intermédias.

Quando um destes testes passa, a conclusão é "a lógica está certa para as
formas que o teste usou". Diz quais formas foram reais e quais foram assumidas.

## Sinais de que a prova está a mentir

- Uma falha que não corresponde a nenhum sintoma observado em produção.
- Uma correção que só mexe no ambiente da prova e "resolve".
- Uma conclusão forte ("a versão X está partida") tirada de uma única
  topologia que ninguém comparou com produção.
- Dados sintéticos que nunca exercitam o caminho que vai correr em produção.
- Testes verdes de um helper cujas entradas, permissões ou respostas foram
  todas escritas pelo próprio autor do helper.

## Quando não aplicar

Se a decisão não depender do ambiente (lógica pura, parsing, cálculos), um
teste unitário chega. O custo de reproduzir produção justifica-se quando a
conclusão autoriza ou bloqueia uma alteração real.

## Relacionadas (leitura opcional, se disponíveis)

- `verify-against-the-host`: confrontar uma proposta com o estado instalado.
- `stateful-service-migrations`: quando o estado de partida faz parte do risco.
