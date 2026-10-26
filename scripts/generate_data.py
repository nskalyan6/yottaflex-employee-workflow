from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.generator import generate_dataset

if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()
    print(json.dumps(generate_dataset(scale=args.scale, seed=args.seed), indent=2))
