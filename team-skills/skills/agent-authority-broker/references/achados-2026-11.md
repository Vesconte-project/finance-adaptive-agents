# Achados verificados (2026-11)

Ambiente: plataforma de agentes Paperclip auto-alojada num portátil com WSL2, PostgreSQL 16
local, contentores Docker numa rede interna atrás de um gateway, publicação de PRs por uma conta
de máquina. Os resultados valem para essa versão e configuração; confirma no teu ambiente.

| Hipótese | Resultado | Consequência |
| --- | --- | --- |
| A conta de máquina consegue fazer merge para `main` | Confirmado em dois repositórios | Regras do ramo com revisão humana, sem bypass; no caso, exigiam plano pago e não foram aplicadas — merge sem ferramenta para agentes em contentor, cooperativo no host |
| A credencial de subscrição montada traz outros tokens | Confirmado (entradas OAuth de outros serviços) | Montar ficheiro derivado mínimo |
| Workflows expõem segredos a PRs internos | Confirmado em dois workflows | `.github/**` passa a `ask_first` |
| Agente altera o próprio comando/perfil/modelo pela API | Refutado na versão instalada | Mantém-se o teste em cada atualização |
| Agente cria agentes ou atribui a um mais privilegiado | Inconclusivo | Lista de rotas no gateway |
| Ferramentas do lado do fornecedor contornam o broker | Inconclusivo | Registar como limite conhecido |

## Rede Docker no WSL

O endereço `host.docker.internal` (Docker Desktop) não alcançou de forma fiável serviços que
escutam no loopback do WSL: o gateway devolvia 502. A correção que funcionou: dois sockets Unix
privados (modo 0600, diretório 0700) geridos por unidades `systemd` de socket, com
`systemd-socket-proxyd` a reencaminhar para as portas do loopback; o gateway monta só esse
diretório. Os serviços continuam a escutar apenas no loopback.

## Provas de ponta a ponta

- Leitura: um agente orquestrador num contentor leu o estado através de plataforma →
  contentor → gateway → broker, com token por execução.
- Escrita: um agente implementador entregou um bundle Git sem receber o token de publicação; o
  broker validou-o, publicou o ramo, abriu o PR e guardou o SHA remoto como recibo.
- A chave estática anterior e tokens ausentes, expirados ou de outro espaço devolveram 403.

## Aprovação, custódia e proxy (fases 9–11)

- **Hardware de aprovação recusado pelo dono** (custo) e, na análise, insuficiente: no mesmo
  host os agentes com o UID do dono alteram a lista de chaves aceites. Substituído por aprovação
  pelo WhatsApp: o broker envia o texto gerado da ação guardada pela API oficial e só aceita uma
  resposta assinada pela Meta (`X-Hub-Signature-256`), do número do dono, em resposta à mensagem
  original, com código HMAC sobre digest, id e epoch.
- **O assistente pessoal tinha dois modos de WhatsApp:** sessão ligada por QR (biblioteca de
  WhatsApp Web, sem assinatura do fornecedor) e Cloud API (webhook assinado). Só o segundo dá uma
  prova que nenhum modelo fabrica.
- **Cofre alojado** (Bitwarden Secrets Manager, plano gratuito): conta na região UE; o servidor
  por omissão devolveu `invalid_client`. A CLI oficial corre em Docker com o token passado por
  nome de variável. A importação copia sem apagar os originais.
- **Proxy MCP:** sessões interativas com token próprio emitido só pelo socket do host, perfil
  `implementer-interactive`, lista fechada de leituras por ligação; erros do fornecedor
  substituídos por códigos fixos; resposta recusada se contiver a credencial.

## PostgreSQL gerido e clientes em Docker

- O plano de controlo do Neon recusa verificadores SCRAM já calculados (`CREATE ROLE … PASSWORD
  'SCRAM-SHA-256$…'` falha no commit com XX000). Cria o login com a palavra-passe gerada,
  enviada por stdin ao `psql`, nunca em argumentos.
- Um contentor cliente com `--cap-drop=ALL` corre como root sem `CAP_DAC_OVERRIDE` e não lê um
  ficheiro 0600 do utilizador do host: o libpq reporta «service file not found». Corre com
  `--user "$(id -u):$(id -g)"`.
- Clientes PostgreSQL por imagem oficial: `docker run` custou cerca de 1,1 s por chamada; um
  contentor cliente persistente com `docker exec` cerca de 0,3 s. Para um broker que faz uma
  chamada por operação, usa o contentor persistente ligado ao ciclo de vida da unidade.
