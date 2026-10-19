# Inventário mínimo de pull steps Git

Usa este exemplo Python 3 apenas depois de confirmar que a resposta autorizada
é uma lista de deployments com `pull_steps`, e que o identificador de step
`prefect.deployments.steps.git_clone` corresponde à implementação instalada.
Outros nomes de step/esquemas precisam de adaptação verificada, não equivalência
inferida. A presença de `commit_sha` aqui não prova que a versão do step o
suporta: confirma a assinatura e a resolução real antes de declarar pinning.

O programa lê JSON de stdin e imprime **uma** projeção JSON só depois de validar
a entrada inteira. Guarda-o num ficheiro temporário autorizado e fornece stdin
separadamente; não combines heredoc de código com pipe de dados no mesmo stdin.
Não recolhe a API, pagina nem determina a janela de restart. O chamador tem de
verificar transporte, paginação e completude, limitar o volume antes de ler e
proteger o input original. Falha nonzero com mensagem fixa significa inventário
não verificado; não existe output parcial útil após erro.

A identidade exposta é `sha256` de protocolo/host/porto/modo de path/path canonicalizados,
sem userinfo, query ou fragment. Não se imprime URL, nome de deployment,
credenciais, branch ou outros campos livres. Serve para agrupar e comparar com
uma origem conhecida transformada pela mesma função, não para provar acesso,
igualdade entre aliases SSH ou identidade de conteúdo. Mesmo paths/hosts podem
conter segredos: por isso ficam também atrás de um digest, que é pseudonimização,
não garantia de anonimato. Trata o relatório como evidência interna.

São aceites URLs http/https/ssh/git e a forma SSH scp `user@host:path` ou
`host:path`; caminhos locais ou sintaxes ambíguas falham explicitamente.
Caracteres de controlo, incluindo os percent-encoded, são rejeitados. A
normalização é conservadora: distingue o path relativo de `host:repo` do absoluto
`host:/repo` ou `ssh://host/repo`; não resolve aliases nem remove `.git`/slashes.
Remover userinfo é deliberado: o digest agrupa localizações sem distinguir contas,
portanto não prova equivalência entre origens dependentes da identidade de login.
Commit omitido ou null resulta em `unpinned`; texto não hexadecimal completo
resulta em `unresolved_revision` sem imprimir o valor. `pinned_literal` significa
apenas SHA literal completo observado, não prova de checkout/executabilidade.

```python
import hashlib
import json
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit

STEP = "prefect.deployments.steps.git_clone"


def clean_text(value):
    if not isinstance(value, str) or not value:
        raise ValueError
    if any(unicodedata.category(c).startswith("C") for c in value):
        raise ValueError
    return value


def repository_identity(value):
    value = clean_text(value)
    clean_text(unquote(value))
    if "://" not in value:
        # Conservative scp syntax; reject local/Windows paths and ambiguous hosts.
        match = re.fullmatch(r"(?:[^/@:\s]+@)?([A-Za-z0-9][A-Za-z0-9._-]*):(.+)", value)
        if not match or len(match.group(1)) == 1:
            raise ValueError
        host, path = match.groups()
        if path == "/":
            raise ValueError
        mode = "absolute" if path.startswith("/") else "scp-relative"
        identity = ["ssh", host.lower(), None, mode, path]
    else:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https", "ssh", "git"}:
            raise ValueError
        host = parsed.hostname
        if not host or not parsed.path or parsed.path == "/":
            raise ValueError
        clean_text(host)
        port = parsed.port  # Invalid ports fail without echoing the input.
        identity = [parsed.scheme.lower(), host.lower(), port, "absolute", parsed.path]
    canonical = json.dumps(identity, ensure_ascii=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def inventory(data):
    if not isinstance(data, list):
        raise ValueError
    rows = []
    for deployment in data:
        if not isinstance(deployment, dict) or "pull_steps" not in deployment:
            raise ValueError
        steps = deployment["pull_steps"]
        if steps is None:
            steps = []
        if not isinstance(steps, list):
            raise ValueError
        for step in steps:
            if not isinstance(step, dict):
                raise ValueError
            if STEP not in step:
                continue
            config = step[STEP]
            if not isinstance(config, dict) or "repository" not in config:
                raise ValueError
            repo_id = repository_identity(config["repository"])
            commit = config.get("commit_sha")
            if commit is None:
                pinning, safe_commit = "unpinned", None
            else:
                commit = clean_text(commit)
                if re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", commit):
                    pinning, safe_commit = "pinned_literal", commit.lower()
                else:
                    pinning, safe_commit = "unresolved_revision", None
            rows.append({"repository_id": repo_id, "pinning": pinning,
                         "commit_sha": safe_commit})
    return {"deployments_examined": len(data), "git_steps_examined": len(rows),
            "other_steps_not_assessed": True, "git_steps": rows}


def main():
    try:
        result = inventory(json.load(sys.stdin))
    except (ValueError, TypeError, KeyError, UnicodeError, OSError, RecursionError):
        print("Inventário não verificado: entrada ou schema inválido.", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Zero git steps pode significar deployments sem clone, outro mecanismo de código
ou outro identificador de step; não concluas que o código está fixado. O
relatório não substitui comparação com origem/release esperada nem prova do
commit efetivamente executado.

Sintaxes verificadas na [documentação Git de URLs](https://git-scm.com/docs/git-clone#_git_urls), consultada em 2026-10-20; configuração SSH e regras Git `insteadOf` exigem confirmação separada.
