# Validation report

Run `python scripts/generate_data.py --scale 0.1 --seed 20261022` and then `python scripts/validate_data.py`. Copy the resulting summary into this document before final submission.

The validator prints:
- table row counts
- primary-key and foreign-key errors
- warnings for deliberately generated exceptions
- dependency graph acyclicity
- overdue task count and declared SLA breach count
- active asset assignment conflict count
- terminated employees with active access
- ground-truth issue count and types

Do not describe the project as passing until you have run it locally and reviewed the actual report.
