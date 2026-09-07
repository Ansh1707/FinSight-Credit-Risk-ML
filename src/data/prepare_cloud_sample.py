"""Create a bounded, deterministic upload sample without modifying raw data.

Run: python -m src.data.prepare_cloud_sample
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from cloud.databricks.workflow import SOURCE_COLUMNS


def run(limit=20000):
    if not 100 <= limit <= 50000:
        raise ValueError("Choose between 100 and 50,000 rows.")
    source = Path("data/raw/application_train.csv")
    if not source.exists():
        raise FileNotFoundError("Place your legitimately obtained application_train.csv under data/raw/ first.")
    selected = pd.DataFrame()
    total = 0
    for chunk in pd.read_csv(source, usecols=SOURCE_COLUMNS, chunksize=50000):
        total += len(chunk)
        if chunk.SK_ID_CURR.isna().any():
            raise ValueError("Raw source contains a missing applicant ID.")
        chunk["_sample_order"] = pd.util.hash_pandas_object(chunk.SK_ID_CURR, index=False).to_numpy()
        selected = pd.concat([selected, chunk]).sort_values(["_sample_order", "SK_ID_CURR"]).head(limit)
    if selected.SK_ID_CURR.duplicated().any() or set(selected.TARGET.unique()) != {0, 1}:
        raise ValueError("Sample must contain unique applicants and both target classes.")
    selected = selected.drop(columns="_sample_order").sort_values("SK_ID_CURR")
    out = Path("data/processed/cloud_sample.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    Path("reports").mkdir(exist_ok=True)
    selected.to_csv(out, index=False)
    summary = {"source_rows_scanned": total, "sample_rows": len(selected),
        "sample_default_count": int(selected.TARGET.sum()), "columns": SOURCE_COLUMNS,
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "sampling": "smallest deterministic pandas ID hashes; not stratified; no labels used in selection",
        "pandas_version": pd.__version__, "numpy_version": np.__version__}
    Path("reports/cloud_sample_manifest.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Saved {len(selected):,} rows to ignored {out}. Upload only after reviewing dataset terms.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=20000)
    run(parser.parse_args().limit)
