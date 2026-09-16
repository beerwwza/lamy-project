---
name: to-spec
description: "Turn an agreed LAMY requirement into a testable spec."
disable-model-invocation: true
---

Turn the current conversation and codebase understanding into a testable spec.
Do not restart discovery with a broad interview. Ask only a targeted blocking
question when a missing answer would change the data model, user behavior, or
security boundary.

The issue tracker and triage label vocabulary should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.

## Process

1. Read `AGENTS.md`, the relevant `CLAUDE.md` section, and nearby code/tests.
	Use the project's domain glossary vocabulary and respect existing ADRs.

2. State the user-visible problem, the smallest coherent solution, affected
	Django layers, permissions, data migration needs, and explicit out of scope.

3. Sketch the highest useful behavior seam for testing. Prefer existing Django
	test patterns; identify the cheapest check that could disconfirm the design.
	Include `python manage.py check`, migration checks, and focused tests where
	relevant.

4. Present the draft for approval when the seam, scope, or acceptance criteria
	are materially uncertain. Do not publish or create tickets until approved.

5. Publish to the configured tracker only after approval. If no tracker is
	configured, save a local spec under `.scratch/<feature-slug>/spec.md` when
	the user asks for a durable artifact; otherwise return the spec in chat.
	Apply the `ready-for-agent` label when the tracker supports it.

<spec-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this spec.

## Further Notes

Any further notes about the feature.

</spec-template>
