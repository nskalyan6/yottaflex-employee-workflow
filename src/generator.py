"""Deterministic synthetic employee onboarding/offboarding data generator."""
from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable


SEED_DEFAULT = 20261022
BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "data" / "generated"
TRUTH_DIR = BASE_DIR / "data" / "ground_truth"

DEPARTMENTS = [
    ("DEP-001", "Engineering"), ("DEP-002", "IT"), ("DEP-003", "Human Resources"),
    ("DEP-004", "Finance"), ("DEP-005", "Operations"), ("DEP-006", "Sales"),
    ("DEP-007", "Facilities"), ("DEP-008", "Customer Support"),
]
ROLE_NAMES = [
    "Software Engineer", "IT Support Analyst", "HR Specialist", "Finance Analyst",
    "Operations Coordinator", "Sales Representative", "Facilities Technician",
    "Customer Support Agent", "Engineering Manager", "Security Analyst",
    "Data Analyst", "Product Manager",
]
LOCATIONS = ["Hyderabad", "Bengaluru", "Pune", "Remote"]
EMPLOYMENT_TYPES = ["permanent", "contractor"]
TASK_NAMES = [
    "Identity verification", "Background check", "Manager confirmation",
    "Create user account", "Provision role access", "Assign laptop",
    "Security training", "Facilities orientation",
]
TASK_DEPENDENCIES = {
    "Create user account": ["Identity verification"],
    "Provision role access": ["Create user account"],
    "Assign laptop": ["Manager confirmation"],
    "Facilities orientation": ["Manager confirmation"],
}
TASK_SLA_DAYS = {
    "Identity verification": 2, "Background check": 5, "Manager confirmation": 2,
    "Create user account": 1, "Provision role access": 1, "Assign laptop": 2,
    "Security training": 5, "Facilities orientation": 3,
}
DATE_BASE = date(2026, 1, 1)


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _iso(value: date | datetime | None) -> str:
    return value.isoformat() if value else ""


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generate_dataset(
    scale: float = 1.0,
    seed: int = SEED_DEFAULT,
    output_dir: Path | str = OUTPUT_DIR,
    truth_dir: Path | str = TRUTH_DIR,
) -> dict:
    """Generate data. scale=0.1 is a quick starter run; scale=1.0 is the target volume."""
    if not 0 < scale <= 1:
        raise ValueError("scale must be > 0 and <= 1")
    out = Path(output_dir)
    truth_out = Path(truth_dir)
    out.mkdir(parents=True, exist_ok=True)
    truth_out.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    first_names = ["Aarav", "Ananya", "Ishaan", "Meera", "Rohan", "Diya", "Arjun", "Kavya", "Vikram", "Nisha", "Rahul", "Priya"]
    last_names = ["Sharma", "Reddy", "Patel", "Rao", "Gupta", "Kumar", "Nair", "Iyer", "Das", "Singh", "Joshi", "Verma"]
    def synthetic_name(index: int) -> str:
        return f"{first_names[index % len(first_names)]} {last_names[(index * 7 + seed) % len(last_names)]}"

    employee_count = max(10, round(500 * scale))
    manager_count = max(5, round(50 * scale))
    case_count = employee_count
    task_count_target = employee_count * 8
    asset_count = max(12, round(600 * scale))
    access_count = max(10, round(300 * scale))

    departments = [{"department_id": d[0], "name": d[1], "effective_from": "2020-01-01",
                    "effective_to": "", "lifecycle_state": "active"} for d in DEPARTMENTS]
    roles = [{
        "role_id": f"ROLE-{i+1:03d}", "name": name,
        "department_id": DEPARTMENTS[i % len(DEPARTMENTS)][0],
        "effective_from": "2020-01-01", "effective_to": "", "lifecycle_state": "active"
    } for i, name in enumerate(ROLE_NAMES)]

    managers = []
    for i in range(manager_count):
        managers.append({
            "manager_id": f"MGR-{i+1:06d}", "employee_id": f"EMP-{i+1:06d}",
            "name": synthetic_name(i), "department_id": DEPARTMENTS[i % 8][0],
            "effective_from": "2024-01-01", "effective_to": "", "lifecycle_state": "active"
        })

    employees = []
    for i in range(employee_count):
        dept = DEPARTMENTS[i % 8][0]
        role = roles[i % len(roles)]
        start = DATE_BASE + timedelta(days=rng.randint(0, 280))
        employees.append({
            "employee_id": f"EMP-{i+1:06d}", "full_name": synthetic_name(i + manager_count),
            "email": f"employee{i+1:06d}@example.test", "department_id": dept,
            "role_id": role["role_id"], "manager_id": managers[i % manager_count]["manager_id"],
            "location": LOCATIONS[i % len(LOCATIONS)],
            "employment_type": EMPLOYMENT_TYPES[i % 2],
            "hire_date": _iso(start), "employment_status": "active",
            "effective_from": _iso(start), "effective_to": ""
        })

    truth = []
    # Deliberate exception: one employee has no manager. This is a nullable FK by design.
    anomaly_employee_ids = {
        "manager_missing": employees[min(4, employee_count - 1)]["employee_id"],
        "task_prerequisite": employees[min(9, employee_count - 1)]["employee_id"],
        "asset_duplicate": employees[min(14, employee_count - 1)]["employee_id"],
        "start_before_check": employees[min(19, employee_count - 1)]["employee_id"],
        "offboarding_access": employees[min(24, employee_count - 1)]["employee_id"],
        "overdue_task": employees[min(29, employee_count - 1)]["employee_id"],
        "department_change": employees[min(34, employee_count - 1)]["employee_id"],
    }
    for emp in employees:
        if emp["employee_id"] == anomaly_employee_ids["manager_missing"]:
            emp["manager_id"] = ""
    truth.append({"issue_id": "ISSUE-000", "issue_type": "manager_missing",
                  "entity_type": "Employee", "entity_id": anomaly_employee_ids["manager_missing"],
                  "employee_id": anomaly_employee_ids["manager_missing"],
                  "expected_decision": "flag_missing_manager_and_route_for_assignment",
                  "description": "Manager relationship is intentionally blank and must be resolved."})

    onboarding_cases = []
    for i, emp in enumerate(employees):
        onboarding_cases.append({
            "case_id": f"ONB-2026-{i+1:06d}", "employee_id": emp["employee_id"],
            "case_type": "onboarding", "created_at": _iso(date.fromisoformat(emp["hire_date"]) - timedelta(days=10)),
            "planned_start_date": emp["hire_date"], "case_status": "in_progress",
            "process_owner": "OPS-001", "closed_at": ""
        })

    task_templates = []
    for i, task_name in enumerate(TASK_NAMES):
        task_templates.append({
            "template_id": f"TMPL-{i+1:03d}", "task_name": task_name,
            "role_id": "", "location": "all", "sla_days": TASK_SLA_DAYS[task_name],
            "prerequisite_task_name": ";".join(TASK_DEPENDENCIES.get(task_name, [])),
            "is_required": "true", "effective_from": "2020-01-01", "effective_to": ""
        })

    task_instances = []
    task_by_employee_and_name = {}
    task_counter_by_case = defaultdict(int)

    for case in onboarding_cases:
        emp = next(e for e in employees if e["employee_id"] == case["employee_id"])
        base = date.fromisoformat(case["planned_start_date"])

        for j, task_name in enumerate(TASK_NAMES):
            task_counter_by_case[case["case_id"]] += 1
            created = base - timedelta(days=8 - j)
            due = created + timedelta(days=TASK_SLA_DAYS[task_name])

            # Start with the original status rules.
            if j < 3:
                status = "completed"
            elif due < date(2026, 10, 26):
                status = "overdue"
            else:
                status = "pending"

            completed_at = (
                _iso(created + timedelta(days=1))
                if status == "completed"
                else ""
            )

            row = {
                "task_id": f"TASK-ONB-{case['case_id']}-{j+1:03d}",
                "case_id": case["case_id"],
                "employee_id": emp["employee_id"],
                "template_id": f"TMPL-{j+1:03d}",
                "task_name": task_name,
                "owner_manager_id": emp["manager_id"],
                "status": status,
                "created_at": _iso(created),
                "due_at": _iso(due),
                "completed_at": completed_at,
                "prerequisite_task_ids": "",
                "sla_breached": "false",
            }

            task_instances.append(row)
            task_by_employee_and_name[(emp["employee_id"], task_name)] = row

    # Resolve prerequisite IDs after all task IDs exist.
    for row in task_instances:
        prereq_names = TASK_DEPENDENCIES.get(row["task_name"], [])
        ids = [
            task_by_employee_and_name[(row["employee_id"], name)]["task_id"]
            for name in prereq_names
        ]
        row["prerequisite_task_ids"] = ";".join(ids)
        row["sla_breached"] = str(
            row["status"] != "completed"
            and date.fromisoformat(row["due_at"]) < date(2026, 10, 26) ).lower()

    # Labelled edge case: account creation completed before identity verification.
    emp_id = anomaly_employee_ids["task_prerequisite"]
    account_task = task_by_employee_and_name[(emp_id, "Create user account")]
    identity_task = task_by_employee_and_name[(emp_id, "Identity verification")]
    account_task["status"] = "completed"
    account_task["completed_at"] = _iso(date.fromisoformat(identity_task["created_at"]) - timedelta(days=1))
    truth.append({"issue_id": "ISSUE-001", "issue_type": "task_completed_before_prerequisite",
                  "entity_type": "TaskInstance", "entity_id": account_task["task_id"],
                  "employee_id": emp_id, "expected_decision": "flag_dependency_violation",
                  "description": "Account creation completion predates identity verification."})

    # Labelled edge case: employee starts before background check completion.
    emp_id = anomaly_employee_ids["start_before_check"]
    bg_task = task_by_employee_and_name[(emp_id, "Background check")]
    emp = next(e for e in employees if e["employee_id"] == emp_id)
    emp["hire_date"] = _iso(date.fromisoformat(bg_task["created_at"]) - timedelta(days=1))
    emp["effective_from"] = emp["hire_date"]
    truth.append({"issue_id": "ISSUE-002", "issue_type": "start_before_background_check",
                  "entity_type": "Employee", "entity_id": emp_id, "employee_id": emp_id,
                  "expected_decision": "flag_start_date_violation",
                  "description": "Hire date precedes background-check completion."})

    # Labelled edge case: overdue task.
    emp_id = anomaly_employee_ids["overdue_task"]
    overdue = task_by_employee_and_name[(emp_id, "Security training")]
    overdue["status"] = "pending"
    overdue["completed_at"] = ""
    overdue["due_at"] = "2026-01-01"
    overdue["sla_breached"] = "true"
    truth.append({"issue_id": "ISSUE-003", "issue_type": "overdue_task",
                  "entity_type": "TaskInstance", "entity_id": overdue["task_id"],
                  "employee_id": emp_id, "expected_decision": "flag_sla_breach",
                  "description": "Pending task due date is in the past."})

    # Department change is represented in history, not by erasing the original department.
    emp_id = anomaly_employee_ids["department_change"]
    changed_emp = next(e for e in employees if e["employee_id"] == emp_id)
    old_dept = changed_emp["department_id"]
    new_dept = DEPARTMENTS[(int(old_dept[-3:]) % 8)][0]
    if new_dept == old_dept:
        new_dept = DEPARTMENTS[(int(old_dept[-3:]) + 1) % 8][0]
    audit_department_change = {
        "audit_event_id": "AUD-2026-10-26-000001", "entity_type": "Employee",
        "entity_id": emp_id, "event_type": "department_changed",
        "event_at": "2026-10-26T09:00:00", "old_value": old_dept, "new_value": new_dept,
        "actor_id": "OPS-001", "issue_type": "department_change_mid_process"
    }
    changed_emp["department_id"] = new_dept
    truth.append({"issue_id": "ISSUE-004", "issue_type": "department_change_mid_process",
                  "entity_type": "Employee", "entity_id": emp_id, "employee_id": emp_id,
                  "expected_decision": "preserve_history_and_review_tasks",
                  "description": "Department changed during onboarding; audit event preserves old/new values."})

    assets = []
    asset_assignments = []
    for i in range(asset_count):
        assets.append({
            "asset_id": f"AST-LAP-{i+1:06d}", "asset_type": "laptop",
            "serial_number": f"SN-{i+1:08d}", "status": "available",
            "location": LOCATIONS[i % len(LOCATIONS)], "effective_from": "2024-01-01",
            "effective_to": ""
        })
    # One normal assignment per first 200 employees (bounded for starter scale).
    assignment_count = min(employee_count, asset_count, 200)
    for i in range(assignment_count):
        emp_id = employees[i]["employee_id"]
        asset_id = assets[i]["asset_id"]
        asset_assignments.append({
            "assignment_id": f"ASG-{i+1:06d}", "asset_id": asset_id,
            "employee_id": emp_id, "assigned_at": employees[i]["hire_date"],
            "returned_at": "", "assignment_status": "active"
        })
        assets[i]["status"] = "assigned"

    # Deliberate duplicate active assignment: same asset assigned to a second employee.
    if employee_count >= 15 and asset_count >= 1:
        emp_id = anomaly_employee_ids["asset_duplicate"]
        asset_assignments.append({
            "assignment_id": f"ASG-{len(asset_assignments)+1:06d}",
            "asset_id": assets[0]["asset_id"], "employee_id": emp_id,
            "assigned_at": "2026-10-01", "returned_at": "", "assignment_status": "active"
        })
        truth.append({"issue_id": "ISSUE-005", "issue_type": "asset_assigned_twice",
                      "entity_type": "Asset", "entity_id": assets[0]["asset_id"],
                      "employee_id": emp_id, "expected_decision": "flag_duplicate_active_assignment",
                      "description": "One asset has two simultaneous active assignment records."})

    access_requests = []
    approvals = []
    for i in range(access_count):
        emp = employees[i % employee_count]
        request_id = f"ACCREQ-2026-{i+1:06d}"
        requested_at = date.fromisoformat(emp["hire_date"]) - timedelta(days=3)
        approval_status = "approved" if i % 4 != 0 else "pending"
        approved_at = _iso(requested_at + timedelta(days=1)) if approval_status == "approved" else ""
        provisioned_at = _iso(requested_at + timedelta(days=2)) if approval_status == "approved" else ""
        access_requests.append({
            "access_request_id": request_id, "employee_id": emp["employee_id"],
            "system_name": ["Email", "HRIS", "CRM", "VPN"][i % 4],
            "requested_at": _iso(requested_at), "approval_status": approval_status,
            "provisioned_at": provisioned_at, "access_status": "active" if provisioned_at else "not_provisioned",
            "revoked_at": ""
        })
        approvals.append({
            "approval_id": f"APR-{i+1:06d}", "access_request_id": request_id,
            "approver_manager_id": emp["manager_id"], "decision": approval_status,
            "decided_at": approved_at, "comments": "Synthetic approval record"
        })

    # Offboarding records for a subset; keep a specific case with active access as a labelled exception.
    offboarding_cases = []
    terminated_count = min(40, max(5, employee_count // 10))
    terminated_ids = {employees[i]["employee_id"] for i in range(employee_count - terminated_count, employee_count)}
    for idx, emp_id in enumerate(sorted(terminated_ids), start=1):
        offboarding_cases.append({
            "offboarding_case_id": f"OFF-2026-{idx:06d}", "employee_id": emp_id,
            "termination_date": "2026-10-20", "case_status": "in_progress",
            "opened_at": "2026-10-18", "closed_at": ""
        })
        emp = next(e for e in employees if e["employee_id"] == emp_id)
        emp["employment_status"] = "terminated"
        emp["effective_to"] = "2026-10-20"

    # Make sure the labelled employee is terminated and has active access even in a small-scale run.
    emp_id = anomaly_employee_ids["offboarding_access"]
    emp = next(e for e in employees if e["employee_id"] == emp_id)
    emp["employment_status"] = "terminated"
    emp["effective_to"] = "2026-10-20"
    if not any(x["employee_id"] == emp_id for x in offboarding_cases):
        offboarding_cases.append({
            "offboarding_case_id": f"OFF-2026-{len(offboarding_cases)+1:06d}",
            "employee_id": emp_id, "termination_date": "2026-10-20",
            "case_status": "in_progress", "opened_at": "2026-10-18", "closed_at": ""
        })
    active_access = next((x for x in access_requests if x["employee_id"] == emp_id and x["access_status"] == "active"), None)
    if active_access is None:
        # Ensure the exception is represented by reassigning a request to the target employee.
        active_access = access_requests[0]
        active_access["employee_id"] = emp_id
        active_access["approval_status"] = "approved"
        active_access["provisioned_at"] = "2026-10-01"
        active_access["access_status"] = "active"
        approvals[0]["decision"] = "approved"
        approvals[0]["decided_at"] = "2026-09-30"
    truth.append({"issue_id": "ISSUE-006", "issue_type": "offboarding_leaves_active_access",
                  "entity_type": "AccessRequest", "entity_id": active_access["access_request_id"],
                  "employee_id": emp_id, "expected_decision": "flag_and_revoke_access",
                  "description": "Terminated employee still has active access."})

    # Task owner is blank when manager is missing; validation reports the exception without a fake ID.
    for task in task_instances:
        if task["employee_id"] == anomaly_employee_ids["manager_missing"]:
            task["owner_manager_id"] = ""
        # Recompute derived SLA values after all deliberate edge-case mutations.
        task["sla_breached"] = str(task["status"] != "completed" and date.fromisoformat(task["due_at"]) < date(2026, 10, 26)).lower()

    # Event/audit log is append-only; the source department is kept in the event.
    audit_events = [audit_department_change]
    audit_counter = 2
    for emp in employees:
        if emp["employment_status"] == "terminated":
            audit_events.append({
                "audit_event_id": f"AUD-2026-10-26-{audit_counter:06d}", "entity_type": "Employee",
                "entity_id": emp["employee_id"], "event_type": "employment_terminated",
                "event_at": "2026-10-20T17:00:00", "old_value": "active", "new_value": "terminated",
                "actor_id": "HR-001", "issue_type": ""
            })
            audit_counter += 1
    for request in access_requests:
        if request["access_status"] == "active" and request["employee_id"] in terminated_ids | {anomaly_employee_ids["offboarding_access"]}:
            audit_events.append({
                "audit_event_id": f"AUD-2026-10-26-{audit_counter:06d}", "entity_type": "AccessRequest",
                "entity_id": request["access_request_id"], "event_type": "active_access_after_termination",
                "event_at": "2026-10-26T10:00:00", "old_value": "active", "new_value": "active",
                "actor_id": "SYS-001", "issue_type": "offboarding_leaves_active_access"
            })
            audit_counter += 1

    tables = {
        "departments.csv": departments,
        "roles.csv": roles,
        "managers.csv": managers,
        "employees.csv": employees,
        "onboarding_cases.csv": onboarding_cases,
        "task_templates.csv": task_templates,
        "task_instances.csv": task_instances,
        "assets.csv": assets,
        "asset_assignments.csv": asset_assignments,
        "access_requests.csv": access_requests,
        "approvals.csv": approvals,
        "offboarding_cases.csv": offboarding_cases,
        "audit_events.csv": audit_events,
    }
    for filename, rows in tables.items():
        _write_csv(out / filename, rows)

    # Ground truth is separate from generated input data.
    _write_csv(truth_out / "ground_truth.csv", truth)
    manifest = {
        "generator": "src/generator.py", "seed": seed, "scale": scale,
        "generated_at_note": "Synthetic data; fixed dates are intentional for reproducibility.",
        "table_row_counts": {name.removesuffix(".csv"): len(rows) for name, rows in tables.items()},
        "ground_truth_rows": len(truth),
        "source": "Synthetic data generated locally; no external personal data used."
    }
    (out / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    checksums = {p.name: _hash_file(p) for p in sorted(out.glob("*.csv"))}
    (out / "checksums.json").write_text(json.dumps(checksums, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scale", type=float, default=1.0, help="0 < scale <= 1; use 0.1 for a quick run")
    parser.add_argument("--seed", type=int, default=SEED_DEFAULT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--truth-dir", type=Path, default=TRUTH_DIR)
    args = parser.parse_args()
    result = generate_dataset(args.scale, args.seed, args.output_dir, args.truth_dir)
    print(json.dumps(result, indent=2))
