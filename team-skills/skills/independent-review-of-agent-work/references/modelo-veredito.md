# Modelo de veredito e mensagem de volta

## Veredito para o dono

```markdown
**Revisão de <repo> #<n> (`<sha curto>`, base `<sha>` = <instalado | main atual | antigo>)**

**Decisão:** aprovado | aprovado com condições | não aprovado.

**O que está bem** (uma linha por ponto, só o que importa para a decisão)
- …

**Bloqueia** (cada ponto com o risco concreto e o que o resolve)
1. <risco> → <correção> → <teste/prova esperada>

**Para saber** (limites aceitáveis, a documentar; não bloqueiam)
- …

**O que tu tens de fazer** (com hora, quando depender dela)
- Merge entre <hh:mm> e <hh:mm> UTC, com o CI verde em `<sha>`.
- Criar/guardar <credencial> por <método>, nunca pelo chat.

**O que reproduzi:** testes (<n> OK num container sem rede), hashes conferidos, dryrun de <data>
e junção com <PR paralelo>.
**O que não consegui verificar:** …
```

## Mensagem de volta ao autor

```text
<repo> #<n> revisto (<sha>). Aprovado o desenho de <x, y, z>. <n> testes passaram no meu
ambiente <condições>.
Antes do merge/instalação:
1. <correção> — teste esperado: <nome ou comportamento>.
2. …
Não fazer: <alargar o âmbito / force-push / instalar>.
Diz-me o novo SHA; <próximo passo, por exemplo, dryrun pelo agente do servidor>.
```

## Regras práticas

- **Severidade honesta.** Só bloqueia o que pode causar dano, falha silenciosa ou decisão
  errada. Preferências de estilo ficam fora, ou em "para saber".
- **Uma correção, um teste.** Cada bloqueio diz que teste ou prova mostra que ficou resolvido.
  Assim, a revisão seguinte é uma verificação e não uma discussão.
- **Hora explícita.** Se o merge depende de calendários, gates ou janelas, o veredito diz a
  janela. O dono não deve ter de calcular.
- **Não ganhar autoridade.** O revisor recomenda; o merge e a instalação continuam do dono.
- **Quando reproduzir falha por causa do ambiente do revisor,** diz isso e repete com as
  condições corretas antes de bloquear (por exemplo, umask 022 e TMPDIR em disco).
