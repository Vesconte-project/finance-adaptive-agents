# Instalado, carregado e verificado são estados diferentes

**Decisão:** nunca declares aplicada uma configuração que só está instalada.
Confirma a capacidade da unit antes de escolher como carregar a alteração;
segue a estratégia aprovada pelo operador: reload, restart ou reboot pendente.
A ausência de reload não proíbe uma instalação deliberadamente pendente.

## Caso: política de energia num servidor em hardware de portátil

**Evidência:** caso único num host, 16/10/2026, systemd 259.5. Um drop-in
configurou a tampa e a inatividade para serem ignoradas. O reload foi aceite
sem reiniciar o logind; num intervalo de dez minutos, as tentativas de suspensão
passaram de dezenas para zero. Isto não estabelece uma versão mínima para
reload nem prova que todas as propriedades sejam expostas em todas as versões.

Se o serviço for gerido por systemd, consulta a capacidade da unit instalada
(por exemplo, `CanReload` e `Type`) e confirma o mecanismo suportado nessa
versão. Não tentes um restart como substituição automática: pode afetar sessões.
Se a decisão aprovada for esperar pelo reboot, regista “instalado, carregamento
pendente” e a verificação que faltará depois dele.

Confirma valores ativos pela interface do daemon quando disponível. Exemplo
com âmbito **observado no systemd 259 neste host**, não como interface universal:

```bash
busctl get-property org.freedesktop.login1 /org/freedesktop/login1 \
  org.freedesktop.login1.Manager HandleLidSwitch
```

Confirma a exposição de cada propriedade na versão alvo antes de a consultar.
Não uses o sucesso desta consulta como prova de que o resto da política também
foi carregado. `cat-config` mostra os ficheiros e a sua composição, não o estado
do processo. Mede também o sintoma antes/depois num intervalo comparável;
ausência de eventos só é conclusiva se a condição que os provocava continuar.

Num host onde a política aprovada impede suspensão, máscaras dos targets podem
ser uma segunda camada; não as cries ou retires sem confirmar dependências e
autorização. A sua presença não prova que o logind deixou de tentar suspender.

## Sinais de falha e limites

Ficheiro certo com comportamento antigo, reload não suportado e sucesso
declarado antes de um reboot pendente são sinais de verificação incompleta.
Exige três provas distintas: conteúdo instalado, carregamento pelo mecanismo
aprovado e efeito observado. Em caso de falha, conserva o estado pendente em
vez de reiniciar sessões para fazer desaparecer o aviso.

**Não aplicar:** erros de parsing ainda não resolvidos ou programas que leem
deliberadamente a configuração a cada execução. Confirma o ciclo de vida real;
não imponhas um reload a qualquer ferramenta que use um ficheiro.

Para confirmar o âmbito desta versão, consulta a [unit upstream v259](https://github.com/systemd/systemd/blob/v259/units/systemd-logind.service.in)
e as [propriedades D-Bus v259](https://github.com/systemd/systemd/blob/v259/src/login/logind-dbus.c).
Isto não substitui a inspeção da unit e da interface realmente instaladas.
