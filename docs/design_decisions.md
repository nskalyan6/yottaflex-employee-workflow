# Design decisions

1. **Synthetic-only data:** no personal or external source data is used.
2. **Fixed seed:** Python `random` and Faker are seeded to support repeatable output.
3. **Master data first:** departments, roles, managers, and employees are generated before transaction records.
4. **Stable identifiers:** all generated entity IDs use explicit prefixes and zero-padded counters.
5. **Ground truth is separate:** known anomaly labels are exported to `data/ground_truth/ground_truth.csv` and are not used by the validator to decide whether an anomaly exists.
6. **Exceptions remain referentially understandable:** missing manager is represented as a blank optional FK, not a fabricated manager ID. Duplicate assignment is represented as two assignment records.
7. **History is preserved:** department changes and termination are written as audit events.
8. **Trade-off:** this first version is CSV-first to make it easy to inspect. SQLite constraints and normalized task dependency bridge tables are recommended next steps.
9. **Synthetic date anchor:** `2026-10-26` is used as a fixed as-of date so overdue calculations remain reproducible.
