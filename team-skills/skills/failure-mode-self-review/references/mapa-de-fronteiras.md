# Da observação à decisão: tornar a pergunta 3 verificável

Usa este método quando uma decisão operacional depende de informação que atravessa
componentes: importação, normalização, relatórios, planeamento de correções ou publicação.
O resultado mínimo é um mapa curto, um traço adversarial que liga o produtor ao consumidor
reais e uma declaração de onde a prova termina. Não exige reproduzir toda a produção para
rever lógica pura e não substitui verificações autorizadas do ambiente alvo.

## 1. Começa pela decisão e desenha um percurso curto

Escolhe a decisão cujo erro teria consequência: permitir uma correção, fechar um incidente,
aceitar uma exceção ou publicar dados. Identifica o produtor e consumidor concretos, incluindo
os inputs dos chamadores. Para cada fronteira, regista a observação necessária, a transformação
e o significado que o consumidor lhe atribui.

Exemplo extraído de uma regressão sintética relatada:

| Etapa | Observação ou saída | Risco a verificar |
|---|---|---|
| Adaptador real do fornecedor | Contagem de inválidos igual a 1 antes do descarte | A recusa refere-se à resposta completa, não apenas aos sobreviventes |
| Normalização | A linha inválida é descartada; todas as sessões legítimas permanecem | Recalcular qualidade só nos sobreviventes pode produzir zero |
| Diagnóstico e relatório | Datas normalizadas e qualidade anterior ao descarte | O relatório pode preservar datas e perder o motivo de recusa |
| Preview real de correção | Decide se a evidência permite revisão humana | Zero normalizado não pode apagar a recusa original; desconhecido não prova limpeza |
| Aplicação | Recebe o plano bloqueado | Recusar antes de backups ou alterações, conforme o contrato deste processo |

Dois chamadores com o mesmo helper podem fornecer metadados diferentes. Ficheiros de módulo
iguais não demonstram acordo de identidade. Não acrescentes todo o sistema ao mapa: começa
pelo percurso que sustenta a alegação da entrega.

## 2. Segue um caso adversarial pelo percurso real

Escolhe uma perda de significado plausível: dado descartado, campo ausente, identidade
ambígua, agregado dentro da tolerância com resíduos ainda abertos ou estado antigo reutilizado.
Escreve primeiro a decisão esperada e o efeito que tem de permanecer ausente.

1. Introduz o caso na entrada do produtor real, usando dados sintéticos e armazenamento
   descartável quando apropriado, dentro do âmbito autorizado.
2. Faz chegar a saída gerada ao consumidor real. Não reconstruas manualmente uma fixture
   aparentemente equivalente na fronteira cuja ligação queres provar.
3. Observa o significado em cada fronteira e a decisão final. Se houver uma recusa, verifica
   também os efeitos que o contrato proíbe antes dela: backups, remoções ou escritas, por exemplo.
4. Acrescenta um controlo válido que deva avançar até ao estado permitido pelo teste. Bloquear
   tudo não demonstra que a distinção funciona.
5. Identifica alterações manuais de relatórios como testes de resistência adicionais. Não as
   apresentes como saídas normais do produtor.

Uma transformação que retira a linha problemática não justifica apagar a observação negativa.
Isso não torna uma rejeição eterna: uma nova observação validada pode mudar a decisão segundo
o contrato aplicável. Distingue essa nova observação de recalcular o mesmo input reduzido.

Se houver aprovação ou digest, verifica o conteúdo efetivamente ligado ao plano. Um hash
vincula os dados fornecidos; não prova que estavam completos ou corretos. Evidência regenerada
muda o conteúdo a rever e selar. Aprovação anterior não autoriza automaticamente outro plano.

## 3. Declara onde a prova termina

Separa no resultado:

- **Percurso completo exercitado:** entrada, produtor, fronteiras, consumidor e último efeito
  observado, com referência à prova disponível na entrega.
- **Componentes testados à parte:** operações com provas próprias que não foram ligadas ao
  percurso anterior nessa execução.
- **Ligações por provar:** passos necessários para a alegação final ainda não observados;
  indica responsável e condição autorizada de verificação.

Exemplo de declaração limitada: "Download sintético → adaptador real → diagnóstico → relatório
→ preview → recusa de aplicação: bloqueado, sem backups nem alterações. Controlo limpo:
pronto para revisão humana, sem aplicação neste percurso. Aplicação aprovada e restauro:
testes separados. Fornecedor real → aplicação em produção → rebuild → recuperação da página:
por provar."

Não juntes estes resultados numa alegação de recuperação completa de ponta a ponta.

## Caso relatado que motivou o método

A orientação anterior já pedia provas do efeito e de ponta a ponta. O autor tinha-a lido e
não a aplicou à ligação decisiva. Adaptador, recusa do refresh, diagnóstico e preview foram
testados separadamente; as fixtures do preview partiam de frames normalizados construídos à
mão. Até um teste que confirmava recusa e cache inalterada terminava antes do consumidor da
evidência. Mais testes verdes e uma base real não preenchiam essa lacuna.

Na versão defeituosa, o adaptador observava uma linha com fecho nulo e fecho ajustado válido:
contagem de inválidos igual a 1. A normalização descartava-a. O relatório recalculava qualidade
só nos sobreviventes e registava zero; o preview podia ficar pronto para revisão humana.
Todas as sessões legítimas estavam presentes. O defeito era perder uma observação negativa,
não inventar datas nem deixar sessões legítimas em falta.

A correção relatada transportou a observação anterior ao descarte para o relatório. O preview
passou a verificar tanto essa observação como a validação combinada. Campos ausentes ou
malformados ficaram desconhecidos; naquele contrato, só zero inteiro explícito satisfazia a
condição de limpeza. Uma linha sobrevivente sabidamente inválida continuava inválida mesmo
com qualidade original desconhecida. Relatórios antigos sem a secção necessária deixaram de
provar limpeza. As datas continuaram a ser as realmente observadas após normalização.

Naquele adaptador, as populações de inválidos sobrepunham-se e combinar as contagens pelo
máximo evitou dupla contagem. Não copies essa fórmula para populações disjuntas ou métricas
arbitrárias: pede a semântica da combinação.

### Verificação fornecida e limites

Esta é evidência sintética fornecida, não uma execução independente nem uma suite distribuída
com o pacote. O relato inclui reprodução da divergência 1 versus 0 antes da correção e provas
do percurso corrigido com download sintético, adaptador e diagnóstico reais, relatório gerado,
preview real com PostgreSQL e Parquet e tentativa de aplicação de planos bloqueados. A base
era descartável, sem rede, e os preços eram sintéticos; isto não reproduz a topologia de produção.

Foram relatados os seguintes casos:

- fecho nulo com fecho ajustado válido;
- fecho ajustado inválido;
- qualidade desconhecida;
- relatório sem a secção anterior ao descarte;
- zero normalizado em conflito com a recusa original;
- omissão exata limpa como controlo positivo.

Os cinco primeiros ficaram bloqueados, com aplicação recusada antes de backups ou remoções,
bytes da cache e linhas candidatas inalterados. O controlo limpo chegou apenas a
`ready_for_human_review`; não foi aplicado nesse percurso. O caso desconhecido retirou
observações no limite do adaptador. Os casos de secção removida e zero contraditório alteraram
explicitamente o relatório para verificar o consumidor; não eram saídas espontâneas do
produtor corrigido.

O relatório completo contribuiu para o digest da evidência e o hash do plano. Um plano
bloqueado continuou sem poder ser aplicado mesmo com digest correspondente e lease sintética.
Isto verifica a recusa relatada; não valida leases reais nem autoriza aplicação.

Testes separados cobriram aplicação aprovada, restauro, falha parcial e retoma. Não foi
estabelecido um único percurso desde fornecedor real até aplicação em produção, rebuild e
recuperação dos consumidores finais. Permissões, concorrência, leases e inventários de
produção continuaram por verificar. A técnica não garante encontrar todos os modos de falha.

## Outras escolhas de traço, quando relevantes

Dois casos sintéticos fornecidos ajudam a escolher um adversário, sem impor a política daquele
projeto a outros sistemas:

- **Recuperação parcial:** numa fixture PostgreSQL havia 102 sessões pendentes. Restaurar 100
  deixou duas sem fonte. Ao entrar na tolerância agregada, o planeamento começava demasiado
  tarde para voltar a observá-las. Reter as sessões abertas selecionadas dentro do lookback
  já autorizado permitiu verificá-las novamente. Só inserir efetivamente as duas fontes e
  repetir a execução permitiu fechá-las. Deduplicação, cobertura, validade de exceção e
  recuperação são decisões distintas. A ausência de alerta novo não prova recuperação;
  não alargues retenção nem âmbito sem autorização.
- **Identidade entre chamadores:** um produtor resolvia metadados para uma identidade
  canónica, enquanto outro consumidor recebia inputs que resultavam em desconhecido e
  recusava a mesma exceção. Alimentar o consumidor real com a saída real do produtor revelou
  a divergência escondida por fixtures independentes. Inclui inputs efetivos e decisão no
  mapa; partilhar um helper não prova acordo.

Escolhe o traço pela alegação em risco. Esta referência não é uma lista obrigatória de todos
os testes possíveis nem uma autorização para operar os sistemas descritos.
