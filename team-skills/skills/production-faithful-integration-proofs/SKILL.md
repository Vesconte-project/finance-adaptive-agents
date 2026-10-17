---
name: production-faithful-integration-proofs
description: Desenhar ou interpretar uma prova de integração descartável (CI, contentores, base efémera) cujo resultado vai decidir uma alteração em produção, como um pool de ligações, autenticação entre serviços, rede, permissões ou migrações. Usa quando uma prova destas falha ou passa e é preciso saber se a conclusão vale para produção. Não para testes unitários nem para provas sem consequência em produção.
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
- **Versões e identidades:** imagens fixadas por digest; processos não-root
  como em produção.

## Método

1. **Levanta a topologia de produção só em leitura**, com metadados e sem
   segredos: como os processos se ligam, regras de acesso, formatos.
2. **Versiona essa descrição** junto da prova (por exemplo, uma cópia
   sanitizada das regras de acesso) e trata divergências como alterações
   revistas.
3. **Faz a prova afirmar a topologia**, não só o resultado: verifica, por
   exemplo, que o endereço de cliente visto pelo servidor é o esperado. Uma
   prova que reproduz a topologia por acaso deixa de a reproduzir em silêncio.
4. **Compara valores normalizados.** Endereços, tipos e formatos podem vir
   representados de forma diferente (por exemplo um endereço com e sem `/32`);
   normaliza antes de comparar, em vez de afrouxar a verificação.

## Sinais de que a prova está a mentir

- Uma falha que não corresponde a nenhum sintoma observado em produção.
- Uma correção que só mexe no ambiente da prova e "resolve".
- Uma conclusão forte ("a versão X está partida") tirada de uma única
  topologia que ninguém comparou com produção.
- Dados sintéticos que nunca exercitam o caminho que vai correr em produção.

## Quando não aplicar

Se a decisão não depender do ambiente (lógica pura, parsing, cálculos), um
teste unitário chega. O custo de reproduzir produção justifica-se quando a
conclusão autoriza ou bloqueia uma alteração real.

## Relacionadas

- `verify-against-the-host`: confrontar uma proposta com o estado instalado.
- `stateful-service-migrations`: quando o estado de partida faz parte do risco.
