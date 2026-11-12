# Pacote pronto e retoma depois de efeitos sem recibo

Aplica a instalações coordenadas em que o workflow exige procedimentos
versionados e um pacote revisto antes da janela. Não concede acesso ao host,
autoridade para instalar ou autorização para uma recuperação diferente.

## O host observa e executa; o pacote contém a implementação

Um bloco selado pode verificar o pacote e invocar um procedimento. Se ganha
outra implementação de provisioning, instalação ou recuperação em cada janela,
há duas fontes de código para rever e testar. Em workflows com esse contrato,
prepara o procedimento no repositório governante e testa o pacote entregue antes
da janela. Usa o ambiente de desenvolvimento/CI autorizado; se a política exclui
desenvolvimento no servidor de produção, não o substituas por um contentor nesse
mesmo servidor.

O alvo continua a fornecer factos que uma prova externa não adivinha: versões,
mounts, identidades, modos e ancestrais, estado de serviços e recibos. Obtém só
metadados autorizados ou um perfil sanitizado fornecido pelo operador. Plan e
apply usam a mesma admissão da versão alvo; apply relê factos voláteis sob a
coordenação aplicável. Uma divergência relevante bloqueia e volta à revisão do
pacote, em vez de gerar um helper novo para contornar a recusa.

Não confundir esta disciplina com uma capacidade já disponível: se o procedimento
comum ainda não existe, declara a lacuna. Uma recuperação pontual autorizada não
equivale à entrega de um instalador reutilizável.

## A fronteira é o efeito, não a última linha do script

Um passo pode provisionar identidades, reiniciar um serviço e passar as provas,
mas falhar ao gravar o recibo final. Nesse estado, executar a função inteira
porque o recibo falta pode rodar credenciais ou repetir outros efeitos.

- Regista a intenção e os inputs aprovados antes do efeito; guarda o resultado
  durável e a evidência necessária antes de publicar um recibo consumível.
- Distingue não iniciado, efeito confirmado, verificação pendente, concluído e
  efeito indeterminado. Um contador de etapas ou uma pasta existente não basta.
- Na retoma, reconcilia o estado do produtor e dos consumidores. Repete só a
  parte que ficou por concluir, dentro da autorização e dos limites de repetição.
- Se a prova só existiu em memória, não fabriques um PASS para reconstruir o
  recibo. Repete a prova quando isso for seguro e autorizado, explicitando os
  seus efeitos, ou conserva a verificação como desconhecida.
- Uma mudança de fonte ou âmbito exige nova revisão conforme o contrato. Um
  diagnóstico melhor não autoriza aplicar uma recuperação diferente.

Testa interrupções antes do efeito, depois do efeito e depois da prova mas antes
do recibo. Confirma que a retoma não repete provisioning, migrações ou rotação já
confirmados; efeito desconhecido deve bloquear. Não prometas rollback universal
para credenciais, SQL ou efeitos observados externamente.

## Evidência e medição

Numa instalação relatada em novembro de 2026, o passo final falhou porque o
recibo atravessava uma pasta privada inacessível ao worker. Os efeitos anteriores
já tinham acontecido e a prova detalhada não estava persistida. A recuperação
foi delimitada ao final e a novas provas, sem repetir credenciais ou restart.
Fonte de âmbito: [registo operacional](https://linear.app/financestocks/issue/ENG-259)
e [correção do caminho do gate](https://github.com/Vesconte-project/finance-infra/pull/190).
Esse PR e os testes locais não provam que o executor comum foi instalado.

Para avaliar melhoria, separa preparação/revisão de preflight, mutação,
verificação e recuperação. Mede intervenção humana, comandos e correções
surgidas na janela. Não prometas uma duração curta sem medições, nem repitas
suites integrais quando os digests e as fronteiras afetadas não mudaram.
