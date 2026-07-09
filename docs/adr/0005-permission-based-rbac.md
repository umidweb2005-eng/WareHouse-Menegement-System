# ADR-0005 — Permission-Based RBAC with Role Presets

**Status:** Accepted — 2026-07-09

## Context
v1 has three roles (User, Treasurer, Super Admin), but the owner wants future
expansion (e.g., an auditor, a read-only board member, or scoped/regional
treasurers) without code changes. Hardcoding role names into authorization checks
(`if user.is_treasurer`) makes new roles a code change and scatters policy through
the codebase.

## Decision
- Authorization is built on **fine-grained permissions** (`resource.action`),
  grouped into **roles**, assigned to staff.
- **Roles are data**, not code; new roles are inserted as rows.
- Authorization checks are always written against **permissions**, never role
  names (e.g., check `donation.record`, never "is Treasurer").
- Ship three **system presets** (User, Treasurer, Super Admin) seeded with their
  permission sets. The public "User" permission set is granted by default to
  unregistered chats (who are never persisted).
- Permission checks live in the **application layer** so all adapters share them.
- The model anticipates **scoped permissions** (e.g., per-campaign/fund) later,
  by keeping checks abstracted behind the application layer.

## Consequences
- ✅ New roles/permissions are configuration, not redeploys.
- ✅ Uniform enforcement across current and future adapters.
- ✅ Supports future separation of duties (who manages power vs who records money).
- ➖ Slightly more schema and seeding than three hardcoded roles.
- ➖ Requires the discipline of never branching on role names.

See [`USER_ROLES.md`](../USER_ROLES.md).
