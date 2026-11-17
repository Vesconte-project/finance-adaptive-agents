# Observed failure, recovery and limits

## Evidence basis

This lesson comes from a supplied experience handoff dated 17 November 2026 and a supplied independent assessment of the first candidate. It is a sanitized account of one investigation in an organization using a tracker, wiki and multiple repositories. The author did not independently retrieve the underlying systems.

The user asked an agent to investigate operational installation inefficiency seriously across planning sources and repositories. The agent read two issue discussions and one smaller plan, then extracted headings and read roughly eight of about forty sections from a main wiki log of approximately 173,000 characters. It missed linked technical-design and specification pages and the project's long planning body.

The code analysis was accurate: many per-batch installers existed, and several attempts failed on wrapper defects. The agent nevertheless presented a new sequence of work without disclosing the partial planning read. It then refined that proposal in a follow-up answer before retrieving the missing sources.

Only after the user asked whether the wiki had been read did the agent read the omitted material. It contained an existing generic release installer plan, an automation item without its own issue that removed a recurring manual step, four versioned contracts, a mandatory proof-of-concept acceptance gate, and an explicit delivery order. The proposed new sequence had partially rediscovered an established plan.

## Why the failure matters

The consequential error was carrying survey depth into a topic-specific recommendation. Several conditions made that easy:

- Explicit read-first links were not followed through the planning chain.
- Large saved outputs encouraged heading extraction and sampled reading.
- The project summary concealed a much longer planning body.
- Some work existed only in wiki sections or project content because not every item had an issue.
- Accurate repository findings gave an unsupported impression of planning completeness.
- The first proposal anchored subsequent reasoning; refining its steps delayed checking the existing plan.
- No coverage statement exposed the missing foundation before conclusions.

The transferable decision is to establish and disclose planning coverage before recommending work, while keeping code findings and planning claims separate.

## What was verified in the supplied account

Reading the missing pages and project body revealed the existing plan and changed the interpretation of the earlier recommendation. The agent explicitly acknowledged its partial reading.

A read-only context collector was also exercised on the topic. It fetched fourteen documents, including the four omitted planning sources and project content, split them into thirty-six parts, and reported seventy-one unfetched references. Its reported unit suite contained 207 passing tests. This supports the collector's demonstrated retrieval and navigation behavior in that environment; it does not establish that an agent read the returned parts or that every listed reference was required.

Instruction changes and the collector were proposed together. Their pull request was open with CI pending at handoff. No claim of publication, installation or sustained behavioral improvement follows from that state.

## Limits and review triggers

This is a narrow lesson supported by one concrete failure and its recovery. The user's report of similar behavior across agents was not measured in the session. Whether this Skill, the instruction changes or the collector prevent recurrence remains unobserved.

The procedure applies to topics with distributed external planning context. It does not justify exhaustive research for self-contained tasks, reading unrelated history, or treating every hyperlink as a prerequisite. It also does not prescribe a particular integration, API field name or retrieval depth across environments.

The candidate assessment required removing a company-specific designation and narrowing activation to distributed planning topics. The package therefore retains an organization-only catalog audience while describing an organization-independent practice.

A useful later exercise would supply an issue with paginated comments, a project with separate summary and planning body, an oversized wiki log, and a linked specification for work without its own issue. Check whether the investigator finds the existing order, discloses unread material and corrects unsupported claims before proposing phases. Contrast that with a self-contained conversion-script request, which should not activate this Skill. These are proposed validation exercises, not reported successful tests.
