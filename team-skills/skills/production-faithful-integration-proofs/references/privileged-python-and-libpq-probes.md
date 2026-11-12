# Fronteiras de leitores Python e URLs libpq

Aplica apenas quando a prova já autorizada corre Python sob outra identidade ou
constrói uma ligação PostgreSQL. Um leitor pode executar código ou contactar a
base mesmo quando o SQL pretendido é só leitura. Estas verificações não concedem
acesso a credenciais, ficheiros protegidos ou produção.

## Importações a partir de um diretório controlado pelo agente

Um filho chamado com `python -B -c ...` herda normalmente o cwd do pai; `-B`
impede bytecode, não a importação de um json.py ou de um módulo de driver plantado
nesse diretório. Se o filho tem a identidade de serviço e uma credencial real,
isso atravessa a fronteira de privilégios antes do primeiro SELECT.

Quando compatível com o runtime, usa `-I` e um cwd privado/controlado, e valida
também o interpretador, módulos explicitamente carregados, ficheiros e
ancestrais. `-I` não torna confiável código que o próprio programa adiciona ao
sys.path nem é sandbox de código hostil.

Prova com um módulo inofensivo plantado no cwd de origem e um marcador sintético:
a invocação antiga importa-o e a corrigida não o executa. Corre a prova sem
credenciais reais. Regista os caminhos e mecanismos que ficaram explicitamente
no sys.path; não alargues permissões para permitir a importação.

## URI PostgreSQL não é formulário HTTP

Num leitor relatado, `urlencode(query)` converteu os espaços de `options` em `+`.
A libpq recebeu esses sinais literalmente; uma opção pretendida como
`-c default_transaction_read_only=on -c statement_timeout=20000` ficou inválida
antes do inventário de leitura.

Para uma query de URI destinada à libpq, `urlencode(query,
quote_via=urllib.parse.quote)` representa os espaços como `%20`. Isso não prova
que uma reconstrução completa da URI preserve utilizador, password, caminhos,
parâmetros repetidos ou sinais `+` preexistentes. Evita conversões desnecessárias;
quando houver reconstrução, declara que partes são preservadas e como são
interpretadas. Não assumes que o input é URI se o contrato aceita também outro
formato de conninfo.

Testa com um URL sintético completo e o parser do driver real, por exemplo
`psycopg.conninfo.conninfo_to_dict`: `options` tem de resultar exatamente na
string esperada. Inclui uma password sintética com caracteres reservados,
espaços, `+` e `%`, e parâmetros existentes. Nunca imprimas a URI nem o dicionário
resultante de uma credencial real. O teste do parser não abre uma ligação e não
substitui prova de autorização/READ ONLY na base.

## Evidência

As duas falhas foram identificadas num leitor de cache e reproduzidas com inputs
sintéticos no âmbito da [ENG-172](https://linear.app/financestocks/issue/ENG-172),
em novembro de 2026. O operador reportou depois execução read-only com zero
escritas. Isso suporta as correções da invocação/parser; não valida qualquer
driver, URI reconstruída ou código privilegiado que se copie deste relato.
