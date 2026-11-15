"""Execute the Stage 2 notebook in the current virtual environment."""
from __future__ import annotations

import sys
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from nbclient import NotebookClient


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "packages/science/notebooks/02_preprocessing.ipynb"
    nb = nbformat.read(path, as_version=4)
    manager = KernelManager(kernel_name="python3")
    manager.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
    try:
        NotebookClient(nb, km=manager, timeout=120, resources={"metadata": {"path": str(root)}}).execute()
    finally:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
    nbformat.write(nb, path)
    print(f"Executed {path.relative_to(root)}; figures in data/derived/science/phase_2/")


if __name__ == "__main__":
    main()
