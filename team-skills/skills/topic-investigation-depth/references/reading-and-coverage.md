# Read the source chain and expose its boundaries

## Build a source ledger

For an in-scope topic, list the sources required to establish its existing plan. Track each source's role, retrieval status, reading status and unresolved links. Retrieval and reading are separate states: a downloaded file is not a read document.

Use a compact ledger such as:

| Source | Role | Coverage | Consequence |
| --- | --- | --- | --- |
| Issue and comments | Request and later decisions | Full; all comment pages read | Supports the current request |
| Project planning content | Delivery order and work without issues | Not read; access unavailable | Cannot recommend a replacement sequence |
| Wiki operations log | Historical context | Partial; design and decision sections read | Cannot claim the entire log was reviewed |

Use authorized retrieval tools already available in the environment. A context collector can help enumerate sources, but its link depth, export size and retrieval success do not prove complete coverage. Inspect its unfetched-reference and truncation reports.

## Follow the canonical chain

1. Read the issue description and every comment. Follow pagination to its end; an initial response or comment count is not the discussion.
2. Read the parent where applicable and the project's long planning content. Check whether the interface exposes a summary separately from the full body. In the observed environment, an MCP project response labeled the long body as a description, while the underlying API distinguished short description from long content. Verify the actual body rather than relying on field names.
3. Follow every explicit read-first link and every document identified as the topic's plan, specification, decision or design. Follow their relevant design and technical-evidence links as well.
4. Read repository documentation and inspect code cited by those sources. Compare documented intent with implementation; neither establishes the other by itself.
5. Look for work recorded without an issue: provisional IDs, project work lists, milestone sections and dependency tables. Identify the documented sequence and acceptance criteria before drafting a new sequence.

Do not recursively read every unrelated hyperlink. Classify links by their relevance to the topic and the claim you intend to make. A required prerequisite remains a gap until read or explicitly reported as unavailable; a fetcher's depth limit does not make it irrelevant. When relevance is uncertain, inspect enough context to decide and record the boundary.

## Handle oversized and chronological documents

When a tool saves an oversized response to a file, use the available authorized reader to inspect that file. First establish whether it contains the complete export or an already truncated result. If completeness cannot be established, mark it uncertain and obtain the missing material where access permits.

Index headings for navigation. In chronological logs, look for planning, design, specifications, decisions, delivery order, milestones and phase sections, including equivalent terms in the document's language. Then read the required material continuously, using bounded chunks with clear start and end positions. Do not substitute search matches, headings or sampled excerpts for the surrounding argument and decisions.

Read required standalone plans and specifications completely. For a broader historical log, read the relevant sections in full and follow their prerequisite links. Keep unrelated history outside the reading boundary, and label the log as partially read. If the log itself is designated a required read-first document, do not silently downgrade that requirement to a few sections.

Check that chunk boundaries leave no gaps. Expand reading when a section refers to an earlier definition, later amendment or linked decision needed to understand it. Reconcile chronological amendments rather than treating the first or last search match as authoritative without context.

## Compare before recommending

Before proposing implementation phases, establish:

- The existing plan's order, dependencies and acceptance criteria.
- Which items are implemented, in progress or only specified, using available current evidence.
- Whether the proposed work follows that plan, fills a demonstrated gap, or changes it.

Code defects can support a diagnosis without supporting a claim that no plan exists. Search for the existing plan before elaborating a replacement. If required planning material is unavailable, keep any alternative explicitly provisional and identify what must be read before adopting it.

## State coverage before conclusions

Keep the report short but specific:

- **Read in full:** sources and complete comment or document coverage.
- **Read in part:** source names and exact sections or boundaries.
- **Not read or incomplete:** required sources, retrieval failures and unresolved prerequisites.
- **Effect on conclusions:** which findings are supported and which recommendations remain provisional.

For example: “The issue and all comments, project plan and linked specification were read in full. The operations log was read only through its design and decision sections. The linked milestone page was inaccessible. The repository evidence supports the wrapper-defect finding; the final delivery order remains provisional until the milestone page is read.”

Do not infer absence from this ledger. A missing plan, unassigned task or complete understanding requires evidence beyond a partial search. If new reading contradicts an earlier answer, identify the missed source, withdraw or qualify the affected claim, and explain the corrected recommendation.
