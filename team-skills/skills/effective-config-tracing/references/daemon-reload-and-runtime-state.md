# Ficheiro instalado, daemon com o valor antigo

Um ficheiro de configuração correto em disco não prova que o processo o leu.
Um daemon pode precisar de reload ou restart, e a capacidade de reload depende
da versão.

## Caso: política de energia num servidor em hardware de portátil

Um servidor montado num portátil continuava a tentar suspender (dezenas de
tentativas em minutos), embora o drop-in do `systemd-logind` dissesse
`ignore` para tampa, inatividade e teclas de energia. O `cat-config` mostrava
os valores certos; o daemon ainda não os tinha carregado.

- O `systemd-logind` só suporta reload a partir de versões que o declaram
  com `Type=notify-reload` (systemd 253 ou mais recente; confirma na versão
  instalada). Em versões anteriores, um reload não aplica a configuração e um
  restart pode terminar sessões.
- Verifica a capacidade **antes** de instalar a política: lê o `Type` da unit
  e recusa, sem instalar nada, se não for o esperado. Uma instalação parcial é
  pior do que nenhuma.
- Confirma o valor **ativo** pela interface do próprio daemon, não pelos
  ficheiros. Para o logind, por D-Bus:

  ```bash
  busctl get-property org.freedesktop.login1 /org/freedesktop/login1 \
    org.freedesktop.login1.Manager HandleLidSwitch
  ```

  Repete para cada propriedade da política e exige o valor esperado em
  todas.
- Mede o sintoma antes e depois (por exemplo, tentativas de suspensão no
  journal num intervalo fixo). Zero depois do reload é a prova; um ficheiro
  correto não é.
- Num servidor de hardware de portátil, mascarar os targets de suspensão e
  hibernação é uma segunda camada contra caminhos que não passam pelo logind.
  Confirma que nada no host depende deles.

## Generalização

Para qualquer daemon: confirma como aplica configuração nova (reload, restart,
SIGHUP, nada), verifica que a versão instalada suporta esse caminho e lê o
valor efetivo pela interface de runtime. Automação idempotente que só compara
ficheiros vai declarar sucesso numa repetição em que a configuração nunca foi
aplicada.
