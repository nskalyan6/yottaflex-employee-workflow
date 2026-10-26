"""Independent checks for generated synthetic workflow data."""
from __future__ import annotations
import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "generated"
TRUTH_DIR = BASE_DIR / "data" / "ground_truth"
AS_OF = date(2026, 10, 26)


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate(data_dir: Path | str = DATA_DIR, truth_dir: Path | str = TRUTH_DIR) -> dict:
    data_dir, truth_dir = Path(data_dir), Path(truth_dir)
    tables = {p.stem: read_csv(p) for p in data_dir.glob("*.csv")}
    errors, warnings = [], []
    required = ["departments", "roles", "managers", "employees", "onboarding_cases",
                "task_templates", "task_instances", "assets", "asset_assignments",
                "access_requests", "approvals", "offboarding_cases", "audit_events"]
    for name in required:
        if name not in tables:
            errors.append(f"Missing table: {name}")

    def unique(table, key):
        values = [r.get(key, "") for r in tables.get(table, [])]
        duplicates = [v for v, count in Counter(values).items() if v and count > 1]
        if duplicates:
            errors.append(f"{table}.{key} has duplicate values: {duplicates[:5]}")
        if any(not v for v in values):
            errors.append(f"{table}.{key} contains blank primary keys")

    for table, key in [
        ("departments", "department_id"), ("roles", "role_id"), ("managers", "manager_id"),
        ("employees", "employee_id"), ("onboarding_cases", "case_id"),
        ("task_templates", "template_id"), ("task_instances", "task_id"),
        ("assets", "asset_id"), ("asset_assignments", "assignment_id"),
        ("access_requests", "access_request_id"), ("approvals", "approval_id"),
        ("offboarding_cases", "offboarding_case_id"), ("audit_events", "audit_event_id")
    ]:
        unique(table, key)

    ids = {
        "departments": {r["department_id"] for r in tables.get("departments", [])},
        "roles": {r["role_id"] for r in tables.get("roles", [])},
        "managers": {r["manager_id"] for r in tables.get("managers", [])},
        "employees": {r["employee_id"] for r in tables.get("employees", [])},
        "cases": {r["case_id"] for r in tables.get("onboarding_cases", [])},
        "templates": {r["template_id"] for r in tables.get("task_templates", [])},
        "tasks": {r["task_id"] for r in tables.get("task_instances", [])},
        "assets": {r["asset_id"] for r in tables.get("assets", [])},
        "access": {r["access_request_id"] for r in tables.get("access_requests", [])},
    }
    for row in tables.get("roles", []):
        if row["department_id"] not in ids["departments"]:
            errors.append(f"Role {row['role_id']} references missing department")
    for row in tables.get("employees", []):
        if row["department_id"] not in ids["departments"]:
            errors.append(f"Employee {row['employee_id']} references missing department")
        if row["role_id"] not in ids["roles"]:
            errors.append(f"Employee {row['employee_id']} references missing role")
        if row["manager_id"] and row["manager_id"] not in ids["managers"]:
            errors.append(f"Employee {row['employee_id']} references missing manager")
        if row["employment_status"] not in {"active", "terminated"}:
            errors.append(f"Invalid employment status for {row['employee_id']}")
    for row in tables.get("onboarding_cases", []):
        if row["employee_id"] not in ids["employees"]:
            errors.append(f"Case {row['case_id']} references missing employee")
    task_by_id = {r["task_id"]: r for r in tables.get("task_instances", [])}
    task_by_employee_name = {(r["employee_id"], r["task_name"]): r for r in tables.get("task_instances", [])}
    for row in tables.get("task_instances", []):
        if row["employee_id"] not in ids["employees"] or row["case_id"] not in ids["cases"]:
            errors.append(f"Task {row['task_id']} has invalid employee/case reference")
        if row["template_id"] not in ids["templates"]:
            errors.append(f"Task {row['task_id']} references missing template")
        if row["owner_manager_id"] and row["owner_manager_id"] not in ids["managers"]:
            errors.append(f"Task {row['task_id']} references missing task owner")
        for prereq_id in filter(None, row["prerequisite_task_ids"].split(";")):
            if prereq_id not in task_by_id:
                errors.append(f"Task {row['task_id']} references missing prerequisite {prereq_id}")
            elif row["status"] == "completed" and task_by_id[prereq_id]["status"] != "completed":
                warnings.append(f"Completed task {row['task_id']} has incomplete prerequisite {prereq_id}")
        if row["status"] == "completed" and row["completed_at"] and row["prerequisite_task_ids"]:
            completed_at = row["completed_at"]
            for prereq_id in filter(None, row["prerequisite_task_ids"].split(";")):
                prereq_completed = task_by_id[prereq_id]["completed_at"]
                if prereq_completed and completed_at < prereq_completed:
                    warnings.append(f"Task completion precedes prerequisite: {row['task_id']}")
    for row in tables.get("asset_assignments", []):
        if row["asset_id"] not in ids["assets"] or row["employee_id"] not in ids["employees"]:
            errors.append(f"Asset assignment {row['assignment_id']} has invalid FK")
    active_asset_counts = Counter(r["asset_id"] for r in tables.get("asset_assignments", [])
                                   if r["assignment_status"] == "active" and not r["returned_at"])
    for asset_id, count in active_asset_counts.items():
        if count > 1:
            warnings.append(f"Asset {asset_id} has {count} active assignments")
    for row in tables.get("access_requests", []):
        if row["employee_id"] not in ids["employees"]:
            errors.append(f"Access request {row['access_request_id']} references missing employee")
        if row["provisioned_at"] and row["approval_status"] != "approved":
            errors.append(f"Access provisioned without approval: {row['access_request_id']}")
        if row["approval_status"] not in {"approved", "pending", "rejected"}:
            errors.append(f"Invalid approval status: {row['access_request_id']}")
    employees = {r["employee_id"]: r for r in tables.get("employees", [])}
    access_after_termination = []
    for row in tables.get("access_requests", []):
        emp = employees.get(row["employee_id"])
        if emp and emp["employment_status"] == "terminated" and row["access_status"] == "active" and not row["revoked_at"]:
            access_after_termination.append(row["access_request_id"])
    if access_after_termination:
        warnings.append(f"Terminated employees have active access: {access_after_termination}")
    overdue = [r["task_id"] for r in tables.get("task_instances", [])
               if r["status"] != "completed" and r["due_at"] and date.fromisoformat(r["due_at"]) < AS_OF]
    declared_breaches = {r["task_id"] for r in tables.get("task_instances", []) if r["sla_breached"] == "true"}
    if set(overdue) != declared_breaches:
        warnings.append("SLA breach flags do not exactly match overdue task calculation")
    # Dependency graph cycle check with DFS.
    graph = {r["task_id"]: list(filter(None, r["prerequisite_task_ids"].split(";")))
             for r in tables.get("task_instances", [])}
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        for parent in graph.get(node, []):
            if parent in graph and not visit(parent):
                return False
        visiting.remove(node)
        visited.add(node)
        return True
    acyclic = all(visit(node) for node in graph)
    if not acyclic:
        errors.append("Dependency graph contains a cycle")

    truth = read_csv(truth_dir / "ground_truth.csv") if (truth_dir / "ground_truth.csv").exists() else []
    row_counts = {name: len(rows) for name, rows in tables.items()}
    summary = {
        "status": "PASS" if not errors else "FAIL",
        "row_counts": row_counts,
        "primary_and_foreign_key_errors": errors,
        "warnings_and_expected_exceptions": warnings,
        "dependency_graph_acyclic": acyclic,
        "overdue_task_count": len(overdue),
        "declared_sla_breach_count": len(declared_breaches),
        "active_asset_conflict_count": sum(1 for n in active_asset_counts.values() if n > 1),
        "terminated_employee_active_access_count": len(access_after_termination),
        "ground_truth_issue_count": len(truth),
        "ground_truth_issue_types": sorted({r["issue_type"] for r in truth}),
        "as_of_date": AS_OF.isoformat(),
    }
    (data_dir / "validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
