---
name: diagnose-host-failures
description: Catálogo de falhas reais de infraestrutura com sintoma, causa e sonda. Usa quando um comando privilegiado falha sem razão aparente, quando um serviço arranca mas não funciona, quando um health check passa e o sistema está partido, quando o Git recusa um repositório, quando um script deixa de escrever onde escrevia, quando reiniciar um serviço para outros, quando um worker parece saudável e não executa trabalho, quando um CI fica vermelho por algo que funcionou como desenhado, ou quando uma verificação de segurança devolve PASS e nunca recusou nada.
---

# Diagnosticar falhas de host

Antes de teorizar, procura aqui. São falhas observadas em produção, com o
sintoma tal como aparece, a causa, a sonda que confirma, e a correção certa —
que muitas vezes **não** é a primeira que ocorre.

O catálogo completo está em `references/catalog.md`. Lê-o inteiro na primeira
vez: tem 28 entradas e demora quatro minutos.

## Índice por sintoma

**Privilégios**
- `sudo: The "no new privileges" flag is set` → `NoNewPrivileges` na unit mata o setuid.
- Root recebe `Read-only file system` → `ProtectSystem=strict` aplica-se também aos filhos root.
- Um sudoers estreito não protege nada → a identidade está em `docker` ou `lxd`.

**systemd**
- Serviços pararam sozinhos depois de reiniciar outro → `Requires=` propaga o stop, o start não os repõe.
- Um PR endurece uma unit e na verdade remove hardening → o ficheiro do repo estava desatualizado.

**Git**
- `fatal: detected dubious ownership` → dono do repositório diferente de quem executa.
- Uma chave de deploy tinha escrita sem ninguém saber → confirma com `push --dry-run`.

**Python e empacotamento**
- `bad interpreter: No such file or directory` num CLI da release → shebang do diretório de staging.
- Script root a correr de um diretório do utilizador → `sys.path[0]` permite substituir módulos.

**Workers e orquestração**
- Ativação "verificada" em menos de um segundo → aceitou o heartbeat do processo anterior.
- O symlink aponta para a versão nova e corre código antigo → as definições clonam um SHA antigo.
- Todos os jobs falham no clone depois de mudar a identidade do serviço → faltam aliases SSH.
- Runs presas em RUNNING há meses → o worker morreu sem transição de estado.

**Configuração em camadas**
- Trabalhos falham num caminho que não está na configuração do host → o valor vem das definições do orquestrador.
- Uma password aparece na API do orquestrador → referências a cofre resolvidas na publicação.
- Um symlink correto e acesso negado → falta travessia num diretório acima.

**Aplicações**
- O serviço está vivo, a API responde, e o dashboard dá 404 → quer escrever dentro do pacote instalado.

**Guardas e credenciais**
- Um scanner de segredos com `PASS` que nunca disse NÃO → não consegue ler os inputs.
- Uma chave sensível não detetada → a regra adivinha por sufixo do nome.
- `InvocationID` vazio logo após a unit correr → unit transitória descarregada.
- `baseline drift` num lote cujo alvo já está instalado → dois lotes no mesmo ficheiro.
- Deploy falha com `exit status 128` e o serviço não pode reiniciar → apagaram a deploy key do serviço.
- A identidade que corre os flows pode empurrar para o ramo principal → chave partilhada com escrita.

**Sinais para fora da máquina**
- CI vermelho num deploy que funcionou como desenhado → falta `SuccessExitStatus=` para o estado "adiado".
- Um componente novo e os outros antigos, sem erro → o adiamento do primeiro abortou os pedidos seguintes.
- Ninguém soube que o deploy adiado entrou → o canal só envia falhas.
- Um check de monitorização cinzento, ou vermelho para sempre → alarme explícito sem reset documentado.

**Dados e agendamentos**
- Uma etapa diária deixou de correr em silêncio → a data de referência é calculada depois da meia-noite UTC.

## Como usar

1. Procura o sintoma literal, não a tua interpretação dele.
2. Corre a sonda antes de mudar o que quer que seja: confirma ou exclui.
3. Aplica a correção indicada. Várias entradas avisam contra a correção
   intuitiva, que costuma ser enfraquecer uma verificação que está certa.
4. Se a falha não estiver aqui e for nova, acrescenta-a no mesmo formato.

## Regra geral que resume metade do catálogo

**Nunca aceites como prova um estado que já era verdade antes da mudança.**
Um processo vivo, um `is-active`, um registo `ONLINE`, um `/health` genérico:
nada disto distingue a versão nova da antiga.
