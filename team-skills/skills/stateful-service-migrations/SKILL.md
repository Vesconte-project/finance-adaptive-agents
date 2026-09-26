---
name: stateful-service-migrations
description: Planear a migração de estado ou artefactos identificados que residem num checkout ou volume implícito sujeito a substituição, limpeza ou recriação. Usa apenas quando esses dados estão confirmados nesse âmbito; consistência, ausência de perda e recuperação dependem de validação específica da aplicação.
---

# Migrar estado com recuperação verificada

Estado dentro de um checkout ou volume implícito pode ser perdido quando o
workflow substitui, limpa ou recria esse caminho. O risco depende do método de
deploy e das garantias de persistência existentes; confirma o comportamento
antes de concluir que todos os deploys são inseguros. Se a migração for
necessária, trata-a como uma operação de dados com cutover e recuperação
planeados e validados conforme a aplicação; este procedimento não garante, por
si só, ausência de perda nem rollback consistente.

## Inventário antes de tudo

Lista cada família de estado com: caminho atual, tamanho, quem escreve, quem
lê, e a variável de configuração que passará a defini-lo. Inclui o que ninguém
menciona: caches, cursores de sincronização, bases locais de ferramentas,
  homes de serviços e volumes de contentores sem nome apenas quando estejam
  dentro do âmbito confirmado e possam ser afetados.

Se a plataforma usar configuração central e units systemd, declara os caminhos
no mecanismo aprovado, com permissões adequadas ao modelo de privilégio. Uma
configuração root-owned carregada pela unit é uma opção, não um requisito
universal. Separa a decisão sobre localização da configuração específica do
runtime.

## Ordem

1. Classifica o estado por criticidade, consistência e possibilidade de
  reconstrução; caches e cursores também podem exigir validação do consumidor.
2. Planeia dados transacionais e bases embebidas segundo as garantias do
  formato e da aplicação.
3. Trata a base de dados principal com o mecanismo de backup/migração suportado
  pela aplicação e valida um restore conforme a política local.

Cada família só é um ponto de paragem se o sistema continuar consistente nesse
estado intermédio. Documenta dependências, escritas pendentes e condições para
retomar antes de dividir a operação.

## Mecânica por família

1. Inventaria caminhos relativos, contagens, bytes, checksums e metadados
  relevantes (proprietário e modos, quando aplicável). Device e inode ajudam a
  identificar a origem, mas mudam necessariamente entre filesystems e não
  devem ser tratados como igualdade após a cópia.
2. Confirma a plataforma, filesystem/volume, ferramenta de cópia, proprietários,
  permissões e autorização do operador. Determina se os consumidores precisam
  de ser parados ou podem ser sincronizados por snapshot/replicação suportados.
3. No mesmo filesystem, `rename(2)` pode fornecer um cutover atómico quando
  origem, destino e aplicação o permitem. Entre filesystems/volumes, copia os
  dados preservando os metadados necessários, mantém a origem intacta e
  verifica a cópia por conteúdo e inventário antes do cutover. Não assumas que
  copiar é inseguro nem apagues a origem como parte da cópia inicial.
4. Se necessário e suportado, mantém um symlink de compatibilidade apenas após
  verificar que o serviço pode usá-lo e que o caminho não expõe dados.
5. Para dados mutáveis, quiesce os escritores ou faz uma sincronização final
  consistente segundo a aplicação; repete a verificação de conteúdo. Não
  compares device/inode entre filesystems; compara caminhos relativos, hashes,
  tamanhos e metadados que a migração deve preservar.
6. Efetua o cutover apenas com autorização. Mantém a origem recuperável até o
  destino e o consumidor estarem validados durante a janela definida.
7. Regista plano, inventário, configuração anterior e checkpoints antes de
  qualquer passo disruptivo, no mecanismo de auditoria disponível; um receipt
  estruturado é opcional e depende do workflow.

Se o cutover falhar, repõe a configuração anterior somente se isso continuar
consistente com as escritas feitas desde o cutover. Se houver dados novos no
destino, reconcilia-os conforme a aplicação; um symlink de volta não desfaz
essas escritas.

## Symlinks de compatibilidade

São uma ponte, não o destino. Usa-os apenas quando consumidores confirmados
dependam de caminhos absolutos e a plataforma os suporte. Regista a decisão no
mecanismo de auditoria disponível e nunca reescrevas dados históricos no mesmo
movimento.

## Bases de dados em contentores

Se o serviço usar um motor de contentores, confirma o engine, versão, driver e
semântica de volume antes de escolher o método; não generalizes comportamento de
um engine para outro. Trata uma mudança de volume como uma migração separada:

- usa um dump lógico fresco, copiado para fora e **relido**, apenas quando o
  engine e a aplicação o suportarem para este
  estado e a consistência do dump estiver confirmada. Caso contrário, usa um
  snapshot ou backup físico consistente suportado pela aplicação, e valida o
  restore antes do cutover;
- imagens fixadas por digest/ID quando a política exigir reprodução exata;
- definições antigas e novas guardadas num local controlado, root-owned apenas
  se a política e a plataforma o exigirem;
- uma opção como `create_host_path: false` apenas se o engine e a versão a
  suportarem e o comportamento for confirmado;
- preservar o volume antigo até haver prova de vida do novo.

## Depois de mover

- Os backups têm de incluir os caminhos novos, e o teste de restauro tem de
  correr **depois** da migração; o anterior já não prova nada.
- Confirma que programas de backup e recuperação executam código revisto a
  partir de uma localização controlada; root-owned é uma opção conforme a
  plataforma e o modelo de ameaça.
- Se uma identidade temporária for necessária para compatibilidade, usa-a só
  com autorização explícita, após confirmar a política de menor privilégio e
  documentar prazo, âmbito e remoção. Um grupo suplementar é apenas uma opção;
  não o uses como ponte padrão.

## Quando não aplicar

Se o estado já vive fora do código e tem localização declarada, salta esta
skill. Se estiveres a pensar mover dados "de passagem", enquanto fazes outra
coisa: não. É a única parte deste trabalho que não se desfaz com um symlink.
