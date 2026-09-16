---
name: grill-with-docs
description: Sharpen an ambiguous LAMY plan through targeted questions and record ADRs and glossary terms.
disable-model-invocation: true
---

# LAMY discovery workflow

Use this skill when a requirement is ambiguous enough that implementation could
change the domain model, workflow, permissions, or operator experience.

1. Read `AGENTS.md`, the relevant `CLAUDE.md` section, nearby models/forms/views,
	and existing docs before asking questions.
2. Ask only the smallest set of targeted questions that separates competing
	designs. Group questions around actor, trigger, state, data ownership,
	validation, failure behavior, and acceptance evidence.
3. Summarize the answers as explicit decisions, unresolved assumptions, and
	out-of-scope items. Use LAMY's Thai domain vocabulary where applicable.
4. Create or update an ADR and glossary only when the user asks for durable
	documentation or the decision will govern future work. Do not invent an
	issue tracker or silently publish artifacts.
5. Hand the agreed result to `/to-spec`; do not implement code from this skill.

The output must include:

- Decision and alternatives rejected
- Domain terms and their meanings
- User-visible acceptance conditions
- Data, permission, and migration implications
- The exact questions still blocking a spec, if any
