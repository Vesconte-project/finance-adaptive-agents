---
name: vercel-cloudflare-production-surface
description: Abrir, rever ou retirar a superfície pública de projetos no Vercel com DNS no Cloudflare, incluindo domínios personalizados, domínios automáticos .vercel.app, Deployment Protection, promoção manual de deployments e a ordem segura para retirar hostnames servidos por Cloudflare Tunnel e Access. Usa quando se associa ou remove um domínio, se verifica o que está exposto ou se limpa DNS antigo; não para falhas de build nem para a configuração do login.
---

# Superfície pública: Vercel com DNS no Cloudflare

A pergunta que interessa é **que endereços servem o quê, a quem, sem login**.
Não se responde pela configuração declarada: testa-se cada URL sem cookies.

## Antes de abrir

1. **Domínios do projeto.** Lista todos os domínios associados, incluindo o
   automático `<projeto>.vercel.app` e variantes acrescentadas sozinhas (por
   exemplo `www.<subdomínio>`). Confirma que estás no projeto certo: o domínio
   automático listado identifica o projeto. Retira o que não deve servir o
   produto.
2. **Deployment Protection.** Confirma o modo atual (não um modo "legacy") e
   testa, sem cookies, os URLs únicos, os aliases de equipa e de branch e o
   domínio automático de produção. Um domínio automático de produção pode
   servir o site sem pedir login mesmo com a proteção ativa; não o presumas
   protegido.
3. **Auto-assign desligado.** Com a atribuição automática de domínios
   desligada, um build de produção fica "Staged" e só passa a servir os
   domínios quando é promovido. Um push de branch nunca deve gerar Production;
   se gerar, para e investiga a configuração do projeto antes de continuar.
4. **Variáveis antes do build.** As variáveis públicas são embutidas no build;
   mudá-las exige um build novo, sem cache quando o HTML gerado depende delas.

## Abrir um domínio

1. Adicionar o domínio no projeto certo; o Vercel mostra o alvo DNS próprio do
   projeto.
2. No Cloudflare, criar exatamente esse registo em **DNS only** quando o
   desenho exigir que a plataforma veja o IP real do visitante.
3. Promover o deployment pretendido (commit e projeto conferidos).
4. Verificar: o domínio público serve o site; o apex redireciona como previsto;
   os URLs de deployment continuam protegidos; o domínio automático foi
   retirado ou está protegido.

## Retirar um hostname servido por Cloudflare Tunnel

A ordem importa. A aplicação do Access pode ser a **única** proteção de um
hostname que o túnel ainda encaminha:

1. retirar a rota (public hostname) do túnel;
2. retirar o registo DNS, se o Cloudflare não o tiver retirado com a rota;
3. confirmar que o hostname já não resolve nem responde;
4. só então apagar a aplicação do Access.

Apagar primeiro a aplicação do Access expõe o serviço, por exemplo um
orquestrador sem login, enquanto a rota existir.

## Limpar DNS antigo

- Registos que apontam para projetos que já não existem (`DEPLOYMENT_NOT_FOUND`)
  e TXT de verificação antigos devem ser apagados: são superfície órfã.
- Distingue grupos antes de apagar: sites, fornecedor de autenticação (por
  exemplo Clerk), email (MX, SPF, DKIM, DMARC). Os de email geridos por um
  serviço de encaminhamento só se retiram desligando esse serviço, e só
  depois de confirmar que nenhuma conta depende desse endereço para receber
  emails de recuperação.
- Nomes de buckets ou recursos que contêm o domínio antigo não são registos
  DNS; não os confundas com superfície web.

## Evidência

Observado a 26/10/2026 na reabertura de dois projetos Next.js no Vercel com DNS
no Cloudflare: o domínio automático de produção serviu o site sem login com a
proteção Standard ativa; deployments de branches apareceram como Production
"Staged" logo após a importação; a variante `www.` de um subdomínio foi
acrescentada sozinha; e um hostname de túnel continuava encaminhado e protegido
apenas pelo Access. Confirma o comportamento atual da Deployment Protection e
da promoção na documentação do Vercel antes de te apoiares nele.

## Relacionadas (leitura opcional, se disponíveis)

- `clerk-vercel-auth-environments`: login a falhar num deployment do Vercel.
- `clerk-fastapi-trust-boundaries`: identidade, Access e prova do IP do visitante.
- `public-site-crawler-backpressure`: tráfego automatizado depois de abrir.
