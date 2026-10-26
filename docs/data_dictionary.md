# Data dictionary (starter version)

All dates use ISO 8601 (`YYYY-MM-DD`); timestamps use ISO 8601 local synthetic timestamps. IDs are strings and immutable. Blank values represent optional values and must not be replaced with fake IDs.

| Entity/table | Primary key | Important fields and rules |
|---|---|---|
| Department | `department_id` | `name` unique; lifecycle state active/inactive; effective dates bound validity. |
| Role | `role_id` | `name`; `department_id` FK to Department; effective dates. |
| Manager | `manager_id` | `employee_id` references the employee identity; department FK; lifecycle state. |
| Employee | `employee_id` | unique synthetic email; department and role FKs; nullable manager FK; location in Remote/Hyderabad/Bengaluru/Pune; employment type permanent/contractor; status active/terminated. |
| OnboardingCase | `case_id` | employee FK; case type onboarding; planned start date; lifecycle status; optional closed date. |
| TaskTemplate | `template_id` | task name; optional role/location scope; SLA in days; prerequisite task names; effective dates. |
| TaskInstance | `task_id` | case and employee FKs; template FK; optional manager owner; status pending/completed/overdue; due/completion dates; prerequisite IDs. |
| Asset | `asset_id` | asset type, unique serial number, status available/assigned; effective dates. |
| AssetAssignment | `assignment_id` | bridge between Asset and Employee; assigned/returned dates; active/returned status. One asset can have history of multiple assignments, but only one active assignment is valid. |
| AccessRequest | `access_request_id` | employee FK; system name; request/approval/provision/revocation dates; access state. Provisioning requires approval. |
| Approval | `approval_id` | access request FK; optional manager approver; decision approved/pending/rejected; decision timestamp. |
| OffboardingCase | `offboarding_case_id` | employee FK; termination date; lifecycle state; opened/closed dates. |
| AuditEvent | `audit_event_id` | entity type and ID; event type/time; old/new values; actor; issue type. Append-only history. |
| Ground truth | `issue_id` | Separate evaluation labels. Never use `issue_type` as an input feature to anomaly detection. |

## Relationship cardinality

- Department 1:N Role, Manager, Employee.
- Role 1:N Employee.
- Manager 1:N Employee and TaskInstance; Employee manager is optional to permit the explicitly labelled missing-manager scenario.
- Employee 1:N OnboardingCase, TaskInstance, AccessRequest, AssetAssignment, and OffboardingCase.
- OnboardingCase 1:N TaskInstance.
- TaskTemplate 1:N TaskInstance.
- Asset 1:N AssetAssignment over time; at most one active assignment at once.
- AccessRequest 1:N Approval (the starter generator creates one approval per request).
- AuditEvent is an append-only event stream referencing an entity by type and ID.
- TaskInstance prerequisite links are a self-referential N:M relationship represented by semicolon-separated IDs in this starter. A production schema should normalize this to a `task_dependencies` bridge table.

## Starter limitations to disclose

The starter version uses CSV files rather than enforcing all constraints in a relational database. It provides deterministic synthetic data and core checks; extend it with a normalized SQLite schema, richer state-transition checks, and complete evaluation metrics before treating it as a production-quality implementation.
