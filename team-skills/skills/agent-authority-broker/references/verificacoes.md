# Checklist antes de chamar "imposto"

Responde a cada ponto com evidência do ambiente real. Sem evidência, a garantia é cooperativa.

**Autorização.** Os pontos 1–3 e 5–7 são leituras. Os pontos 4 e 8 são sondas ativas: só os
executes com autorização explícita do operador e num ambiente próprio ou de teste, nunca em
produção. Sem essa autorização, descreve a sonda e pede-a. Desfazer depois não substitui a
autorização: notificações ou uma aprovação resolvida não se desfazem. Se uma sonda tiver
sucesso inesperado, não leias nem imprimas o conteúdo; regista só que o acesso foi possível.

1. **Onde corre o agente?** Contentor com raiz só de leitura, sem socket Docker, sem
   credenciais de serviços, saída só pelo gateway? Ou no host com o UID dos segredos?
2. **O que está montado?** Lista os ficheiros de credenciais montados e as chaves (nomes, nunca
   valores). Há tokens de serviços que o agente não precisa?
3. **Para onde sai a rede?** Lista de destinos do gateway. Um destino de fornecedor de modelos
   permitido pode dar acesso a conectores ou ferramentas do lado do fornecedor.
4. **Que API da plataforma alcança?** (sonda ativa, ver acima) Com a chave da execução, tenta: alterar a própria
   configuração, criar agentes, criar tarefas para outro agente, resolver aprovações. Desfaz o
   que mudares.
5. **O que a conta de publicação pode fazer no fornecedor Git?** Lê regras do ramo e, no GitHub,
   os rulesets (só leitura; equivalente noutros fornecedores). Um 403 na leitura das regras não prova que estão ativas.
6. **Que segredos a CI expõe** a pushes e PRs de ramos internos? No GitHub Actions: gatilhos
   `pull_request`, `push` e `pull_request_target`; noutros sistemas, o equivalente.
7. **Onde está a chave de assinatura do humano** e quem a consegue ler?
8. **Testes de fuga** (sonda ativa, ver acima) a partir de um contentor na rede interna: internet direta, rotas
   proibidas, broker sem token, portas do loopback do host, socket Docker, diretório de
   segredos. Cada um tem de falhar; regista o que ainda é possível.
