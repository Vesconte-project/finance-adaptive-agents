# Team Skills follow-up decisions

This document records deferred work and decision gates from the selector-scale review. It is not
a commitment to a specific implementation.

## Current position

The current architecture remains the baseline:

- the explicitly selected model owns semantic Skill relevance;
- native deterministic code owns admission, exposure, validation, integrity, and lifecycle;
- selectors receive bounded factual repository evidence plus admitted routing metadata;
- Skill bodies and references are read only after selection;
- the MCP path supports concurrent independent requests without blocking its event loop;
- routing evaluation distinguishes its 200 close-neighbour entries from additional neutral
  scale distractors.

No deterministic keyword matcher, capability ontology, lightweight classifier, or deferred search
layer is part of the current selection path.

## Next measurements

Before changing the selector architecture:

1. Grow or simulate materially different catalogs and retain machine-readable
   `evaluate-routing --json` reports for each supported selector.
2. Measure routing precision, recall, exact match, stability, latency, prompt size, and actual
   provider usage where the provider exposes it.
3. Add adversarial fixtures whose expected Skills occur throughout the catalog, not only inside
   the initial 200-entry semantic fixture.
4. Measure catalog loading and retained memory with representative complete Skill packages.
5. Load-test MCP concurrency, cancellation, timeouts, and session eviction in the intended cloud
   deployment shape.

## Deferred discovery or tool search

Consider deferred discovery when measured catalog prompt size, latency, or provider cost exceeds an
agreed operating budget. Any experiment must preserve these boundaries:

- discovery may reduce the routing metadata shown to the semantic selector;
- it must not become an unreviewed deterministic relevance decision;
- native admission and exact-resource validation remain authoritative;
- recall against a blinded or adversarial fixture must be compared with direct full-catalog
  selection;
- the fallback and failure behavior must be explicit and auditable.

Do not introduce this solely because a synthetic catalog can be made large.

## Repository instruction documents

`AGENTS.md` and vendor equivalents are complementary to Skills: they describe how work must be
performed in a repository or directory, while Skills provide task-selected specialist knowledge.

A future evidence experiment may include a bounded active instruction chain. It must:

- preserve instruction precedence and report conflicts with selected Skills;
- include repository-scoped documents only, never personal instruction files;
- avoid loading every nested instruction document for repository-wide selection;
- normalize vendor-specific discovery without making the core architecture vendor-specific;
- treat document content as bounded evidence for routing, not as permission to bypass native
  controls.

This is not implemented in the current change.

## Lightweight classifiers

Jev or another small classifier is a research option, not a selected dependency or architecture
decision. Evaluate it only against the same public and blinded routing fixtures used for model
selectors. Adoption would require demonstrated quality, stability, portability, provenance, and
operational savings without weakening semantic ownership or deterministic validation.

## Lazy package loading

The current single-revision catalog cache is acceptable until complete-package measurements show a
material parsing or memory problem. If that threshold is reached, prefer separating the routing
index from lazily loaded package contents rather than caching multiple complete catalog revisions.
