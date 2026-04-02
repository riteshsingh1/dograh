#!/usr/bin/env python3
"""Generate deterministic runtime integrity hash for collarx_engine."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


DEFAULT_RELATIVE_FILES = [
    "license/__init__.py",
    "license/cache.py",
    "license/validator.py",
]


def compute_hash(base_dir: Path) -> str:
    digest = hashlib.sha256()
    for rel in DEFAULT_RELATIVE_FILES:
        file_path = base_dir / rel
        if not file_path.exists():
            raise FileNotFoundError(f"Required file missing for hash: {file_path}")
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate COLLARX_ENGINE_SELF_HASH")
    parser.add_argument(
        "--engine-dir",
        default="collarx-engine/src/collarx_engine",
        help="Base directory for collarx_engine sources.",
    )
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional env file path to append COLLARX_ENGINE_SELF_HASH.",
    )
    args = parser.parse_args()

    engine_dir = Path(args.engine_dir).resolve()
    value = compute_hash(engine_dir)
    print(value)

    if args.env_file:
        env_path = Path(args.env_file).resolve()
        with env_path.open("a", encoding="utf-8") as f:
            f.write(f"COLLARX_ENGINE_SELF_HASH={value}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
