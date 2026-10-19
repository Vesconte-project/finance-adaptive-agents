# Evidence, lifecycle, and validation

Capture non-obvious team skills from reliable sources: observed traces, maintained code or
automation, target-compatible official documentation, reproducible tests, or a sanitized
export. Label workspace-, version-, permission-, or provider-dependent behavior as such. Do
not elevate a plausible workaround, a single incident, or a personal preference into a team
contract.

Before changing a Skill, inspect nearby catalog entries and the repository's canonical-format
rules. Preserve unrelated changes. For an update, state what evidence invalidates the old rule
and which task the revised rule improves. For a retirement, distinguish "not yet installed"
from "installed by consumers" and use the defined lifecycle mechanism for the latter.

## Canonical identity and version contract

Treat a catalog's descriptors as a compatibility contract, not free-form metadata. Inspect the
target parser and documentation before changing or requiring a schema. The following concrete
contract belongs to the finance-adaptive-agents catalog; apply it only after confirming that the
target uses this format. Other catalogs may have different descriptors or lifecycle mechanisms:

- the root `team-skills.json` identifies the source and has its own `schema_version`;
- every Skill directory contains `team-skills.json` with the catalog-supported
  `schema_version`, a stable `id`, and lifecycle `state`;
- the directory name must match the portable Skill `name`, while its frontmatter contains only
  the fields supported by the canonical parser.

Keep the target catalog's stable identity across ordinary content changes. In the format above,
the canonical Git revision and package digest are the durable provenance of materialized
content; do not invent another version field or provider-specific frontmatter. Change a schema,
descriptor shape, or lifecycle meaning only as an explicit contract change with corresponding
compatibility and distribution validation, rather than assuming this format for another bank.

Validate proportionally:

1. check portable package layout, frontmatter, stable identity, and allowed resource types;
2. run focused catalog and safety tests;
3. run broader packaging/distribution tests when canonical contracts or lifecycle behavior
   changed;
4. inspect the diff for secrets, private identifiers, unrelated edits, and misleading claims;
5. if realistic behavior is materially uncertain, use a controlled independent exercise before
   strengthening the canonical rule.

Do not call a change deployed, synchronized, or proven in a target workspace merely because
its files were authored or its local validation passed. Commit and publish only with explicit
authorization.
