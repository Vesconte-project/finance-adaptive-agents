# Recuperação de sessões residuais

Lê esta referência quando uma recuperação parcial faz o agregado voltar à tolerância e o
planeador pode deixar de visitar sessões com faltas ainda abertas. O objetivo é preservar
a observação dessas faltas dentro do âmbito autorizado, sem alterar limiares, retenção ou
permissões.

## O mecanismo que falhou

Num caso sintético reportado pelo operador, havia 102 faltas de inputs por listagem/sessão:
100 de um lote do fornecedor e duas independentes. Restaurar o lote resolveu 100. As duas
restantes ficaram abaixo da tolerância agregada. Um planeador que escolhesse o início apenas
pela incompletude agregada podia começar demasiado tarde e nunca voltar a avaliá-las.

A solução reteve sessões pendentes de incidentes abertos das listagens selecionadas dentro
da janela de recuperação já autorizada. Não alargou essa janela nem inventou inputs.

A deduplicação do incidente não resolve esta perda de observação. Neste projeto, a identidade
era a listagem mais a causa normalizada; data de sessão, região e lote não criavam por si
outro incidente. Cada observação e cada sessão pendente continuavam a importar. Uma causa
diferente tinha outra identidade. Noutro domínio, verifica a identidade contratual antes de
adotar esta chave; listagem e entidade não são necessariamente equivalentes.

## Quatro decisões separadas

| Decisão | Evidência necessária | O que não demonstra |
| --- | --- | --- |
| Deduplicar ou notificar | Identidade estável e histórico de observações | Cobertura completa |
| Avaliar cobertura | Inputs efetivamente avaliados para as chaves e sessões do âmbito | Observação de sessões ausentes da avaliação |
| Admitir uma exceção | Aprovação aplicável ao âmbito e causa exatos, com validade atual e revogação consideradas | Chegada dos inputs em falta |
| Declarar recuperação | Nova observação que satisfaz a condição de recuperação para as sessões pendentes | Recuperação de sessões não avaliadas |

Um incidente antigo, aberto ou marcado como permanente não aprova uma exceção. Uma exceção
pode permitir continuar com uma ausência conhecida quando a política do alvo o admite,
preservando a falta no registo bruto. Expiração ou revogação exigem nova decisão mesmo sem
novo alerta.

## Método de revisão e correção

1. **Reconstrói o conjunto pendente.** A partir do ledger compatível com o contrato atual,
   identifica as sessões por resolver dos incidentes abertos das listagens selecionadas.
   Não infiras identidades a partir de registos antigos incompatíveis.
2. **Cruza com os limites existentes.** Retém apenas sessões dentro do início e fim da
   janela de recuperação já autorizada. Junta-as às sessões que o planeador normal iria
   avaliar. Não alargues o lookback, a retenção nem o universo selecionado para obter um
   resultado verde.
3. **Segue uma sessão até à decisão real.** Traça a chave desde o ledger, pelo planeador e
   leitura da fonte, até à avaliação e decisão persistida. Uma listagem selecionada ou
   mencionada nos metadados não prova que a sessão foi lida.
4. **Exige a condição própria de recuperação.** Para ausência de preço neste caso, cada
   sessão anteriormente pendente precisava de preço efetivamente observado pela avaliação.
   O fecho exigia prova para todas essas sessões. Noutro alvo, confirma também os requisitos
   atuais de validade do input. Uma linha noutra sessão, presença genérica em cache ou
   cobertura agregada não substituem essa prova.
5. **Preserva o que não foi demonstrado.** Uma execução de subconjunto ou janela mais curta
   não pode fechar faltas que não avaliou. Conserva o estado pendente; se ficou fora da
   janela autorizada, explicita essa limitação em vez de declarar recuperação ou ampliar
   automaticamente a janela.
6. **Mantém a adjudicação independente.** Reavalia a validade das exceções sem apagar a
   falta bruta. Uma classificação de causa sustentada por nova evidência é distinta de
   recuperação por chegada do input. Idade e silêncio do alerta não são critérios de fecho.

Uma nova observação validada pode alterar a decisão. Estas regras não tornam incidentes
permanentemente inválidos; impedem que uma mudança de seleção ou de agregado seja tomada
por essa observação.

## Prova adversarial no alvo

Usa dados sintéticos e armazenamento descartável. Exercita o planeador, a leitura real,
a avaliação e a persistência do ledger. Um teste isolado de reconciliação pode receber
explicitamente a sessão antiga sem provar que o planeador volta a selecioná-la.

- Abre faltas num lote e em chaves independentes numa sessão antiga.
- Restaura apenas o lote, deixando o agregado dentro da tolerância existente. Confirma
  que só fecham os incidentes demonstradamente recuperados, que os residuais continuam
  sem inputs na fonte e que a janela ainda inclui a sessão pendente.
- Repete sem novos inputs. A falta deve continuar visível sem exigir novo alerta; o gate
  deve aplicar a política vigente.
- Verifica separadamente que excluir uma listagem ou sessão da avaliação não a fecha.
- Se houver exceções, confirma que aprovação preserva a ausência bruta e que revogação
  volta a impedir a continuação quando a política assim exige, mesmo sem incidente novo.
- Insere os inputs sintéticos residuais na fonte efetivamente consumida e repete. Essa
  nova avaliação deve demonstrar a recuperação restante.

As quantidades tornam a regressão visível; não são limiares obrigatórios. Confirma as chaves
e sessões exatas, além das contagens.

## Evidência do caso e limites de verificação

O material fornecido à autoria relata revisão de código e testes, execução sintética e
resultados de CI. Os módulos, testes executáveis, fixtures, DDL e logs de execução não são
distribuídos neste pacote. Esta síntese não constitui uma reprodução independente nem uma
suíte que possa ser executada a partir do Skill.

Segundo esse material, a correção combinou dois mecanismos: selecionar sessões pendentes
de um ledger compatível, limitadas às listagens e janela autorizadas; e adjudicar recuperação
pelas sessões efetivamente avaliadas e pela presença de preço em cada chave pendente.
Selecionar apenas a listagem não bastava.

A prova sintética reportada percorreu o builder real e SQL sobre PostgreSQL descartável,
com tabelas e fixtures do projeto. As asserções descritas exigiam que:

1. Restaurar o lote fechasse 100 incidentes, mantendo dois abertos na sessão antiga.
2. O resultado permanecesse parcial e o gate recusasse a continuação, apesar de o agregado
   ter voltado à tolerância. Essa recusa decorre da política do caso, não de um limiar universal.
3. A janela continuasse a começar na sessão pendente e não existissem preços fonte para
   as duas chaves residuais.
4. Só após inserir os dois inputs sintéticos na tabela fonte e repetir o builder fechassem
   os dois incidentes restantes, com a sessão registada no diagnóstico de recuperação.

Outro teste reportado percorreu builds sucessivos com o ledger persistido: o alerta inicial
foi deduplicado, a falta continuou a ser reconstruída, uma exceção exata permitiu continuar
preservando a cobertura bruta, a revogação voltou a produzir resultado parcial sem incidente
novo e a chegada dos inputs permitiu o fecho. A duração usada nessa fixture não define uma
política de aprovação reutilizável.

A não recuperação por exclusão de sessão ou subconjunto foi descrita como uma condição do
código de adjudicação. O material não relata um teste isolado dedicado a esse caso; inclui-o
na verificação do alvo antes de afirmar que esse percurso foi exercitado. O resumo de CI
reporta aprovação dos testes sintéticos, sem demonstrar todos os cenários sugeridos nesta
referência.

Não foi demonstrada recuperação em produção nem um percurso único completo do fornecedor
real até todos os consumidores reconstruídos. Um teste separado do fluxo diário substituiu
vários builders derivados por gravadores de argumentos; demonstra encaminhamento da janela,
não execução real desses consumidores. Respostas reais, permissões, concorrência e inventários
de produção continuam por verificar.

Esta referência não define durações de aprovação, tolerâncias, autorização para backfill ou
alargamento de lookback. Para causas como input inválido ou histórico ajustado obsoleto,
define e testa a condição própria de recuperação; a mera presença de uma linha não basta.
