---
name: stateful-service-migrations
description: Mover estado e artefactos para fora de checkouts Git ou de volumes implícitos, sem perder dados e com rollback, incluindo bases de dados em contentores. Usa quando serviços correm a partir de repositórios que também contêm dados, antes de adotar releases imutáveis, ou quando o estado de produção não tem localização declarada.
---

# Migrar estado sem perder nada

Enquanto houver dados dentro do diretório do código, nenhum esquema de deploy
é seguro: substituir código arrisca levar os dados atrás. Esta é a parte lenta
e irreversível de qualquer modernização, por isso faz-se primeiro e devagar.

## Inventário antes de tudo

Lista cada família de estado com: caminho atual, tamanho, quem escreve, quem
lê, e a variável de configuração que passará a defini-lo. Inclui o que ninguém
menciona: caches, cursores de sincronização, bases locais de ferramentas,
homes de serviços, volumes de contentores sem nome.

Declara os caminhos num único ficheiro de configuração root-owned, carregado
pelas units. A aplicação passa a consumir nomes de variáveis, nunca caminhos.
É isso que torna possível uma segunda máquina.

## Ordem

1. O que é fácil de repor (caches, diagnósticos, cursores).
2. Artefactos e ficheiros de resultados.
3. Bases embebidas e estado de ferramentas.
4. A base de dados principal, por último, e só com um dump fresco verificado
   fora da máquina.

Cada família é um ponto de paragem seguro. O trabalho pode parar entre
famílias durante semanas sem deixar o sistema incoerente.

## Mecânica por família

1. Inventário e checksums (device, inode, contagens, bytes, hash da árvore).
2. Parar os consumidores.
3. `rename(2)` no mesmo filesystem. Nunca copiar e apagar: não há janela em
   que os dados existam só num sítio incompleto.
4. Deixar symlink de compatibilidade no caminho antigo.
5. Reler o inventário e comparar com o de antes.
6. Arrancar os consumidores e verificar.
7. Escrever um receipt antes de qualquer restart, para o rollback ter base.

Em falha, reverter os renames já feitos e repor a configuração anterior.

## Symlinks de compatibilidade

São uma ponte, não o destino. Existem porque artefactos antigos e ficheiros
históricos contêm caminhos absolutos. Regras: só os explicitamente revistos,
registados no receipt, e nunca reescrever dados históricos no mesmo movimento.

## Bases de dados em contentores

Um volume gerido pelo motor de contentores não pode passar a bind mount por
symlink. Trata-a como transação separada:

- dump lógico fresco, copiado para fora e **relido** antes de começar;
- imagens fixadas por ID exato, nunca por tag;
- definições do contentor antigo e do novo instaladas root-owned, para o
  rollback não depender de um checkout;
- `create_host_path: false` (ou equivalente), para um caminho errado falhar em
  vez de criar uma base vazia que parece saudável;
- preservar o volume antigo até haver prova de vida do novo.

## Depois de mover

- Os backups têm de incluir os caminhos novos, e o teste de restauro tem de
  correr **depois** da migração; o anterior já não prova nada.
- Programas de backup e recuperação não devem correr a partir do checkout.
  Instala-os root-owned, ou continuas a executar código que não é o revisto.
- Se os serviços ainda correrem com a identidade antiga, a ponte de acesso
  (um grupo suplementar temporário) fica registada com obrigação de remoção.

## Quando não aplicar

Se o estado já vive fora do código e tem localização declarada, salta esta
skill. Se estiveres a pensar mover dados "de passagem", enquanto fazes outra
coisa: não. É a única parte deste trabalho que não se desfaz com um symlink.
