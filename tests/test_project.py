import csv
import json
from pathlib import Path
from src.generator import generate_dataset
from src.validator import validate

def read(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def test_small_generation_has_expected_tables_and_edge_cases(tmp_path):
    data, truth = tmp_path / "data", tmp_path / "truth"
    manifest = generate_dataset(scale=0.1, seed=20261022, output_dir=data, truth_dir=truth)
    assert manifest["table_row_counts"]["employees"] == 50
    assert manifest["table_row_counts"]["task_instances"] == 400
    assert len(read(truth / "ground_truth.csv")) >= 5
    assert (data / "source_manifest.json").exists()

def test_reproducible_csv_outputs(tmp_path):
    d1, t1, d2, t2 = tmp_path / "d1", tmp_path / "t1", tmp_path / "d2", tmp_path / "t2"
    generate_dataset(0.1, 20261022, d1, t1)
    generate_dataset(0.1, 20261022, d2, t2)
    for name in ["employees.csv", "task_instances.csv", "assets.csv", "access_requests.csv"]:
        assert (d1 / name).read_bytes() == (d2 / name).read_bytes()
    assert (t1 / "ground_truth.csv").read_bytes() == (t2 / "ground_truth.csv").read_bytes()

def test_validation_reports_known_exception_types(tmp_path):
    data, truth = tmp_path / "data", tmp_path / "truth"
    generate_dataset(0.1, 20261022, data, truth)
    report = validate(data, truth)
    assert report["dependency_graph_acyclic"] is True
    assert report["ground_truth_issue_count"] >= 5
    assert "primary_and_foreign_key_errors" in report
