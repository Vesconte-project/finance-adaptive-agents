# Achados verificados (2026-11)

Ambiente: plataforma de agentes Paperclip auto-alojada num portátil com WSL2, PostgreSQL 16
local, contentores Docker numa rede interna atrás de um gateway, publicação de PRs por uma conta
de máquina. Os resultados valem para essa versão e configuração; confirma no teu ambiente.

| Hipótese | Resultado | Consequência |
| --- | --- | --- |
| A conta de máquina consegue fazer merge para `main` | Confirmado em dois repositórios | Regras do ramo com revisão humana obrigatória, sem bypass para a conta |
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
