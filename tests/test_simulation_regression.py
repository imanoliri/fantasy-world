import json
import os
import pytest
from pathlib import Path

def test_montreia_burgs_regression():
    """
    Regression test to ensure Montreia_burgs.json matches the saved snapshot.
    If the output changes due to new features, the developer has to update the test data
    """
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent
    snapshot_path = base_dir / "tests" / "data" / "Montreia_burgs.json"
    current_path = base_dir / "fantasy_worlds" / "Montreia" / "Montreia_burgs.json"

    # Check if files exist
    assert snapshot_path.exists(), f"Snapshot file not found at {snapshot_path}"
    assert current_path.exists(), f"Current output file not found at {current_path}"

    # Load JSON content
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot_data = json.load(f)

    with open(current_path, "r", encoding="utf-8") as f:
        current_data = json.load(f)

    print("snapshot_data first element")
    print(snapshot_data[0])

    print("current_data first element")
    print(current_data[0])

    # Make sure data hasn't changed
    assert current_data == snapshot_data

def test_montreia_trade_routes_regression():
    """
    Regression test to ensure Montreia_trade_routes.json matches the saved snapshot.
    """
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent
    snapshot_path = base_dir / "tests" / "data" / "Montreia_trade_routes.json"
    current_path = base_dir / "fantasy_worlds" / "Montreia" / "Montreia_trade_routes.json"

    # Check if files exist
    assert snapshot_path.exists(), f"Snapshot file not found at {snapshot_path}"
    assert current_path.exists(), f"Current output file not found at {current_path}"

    # Load JSON content
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot_data = json.load(f)

    with open(current_path, "r", encoding="utf-8") as f:
        current_data = json.load(f)

    # Debug print as requested generally for regression tests
    print("snapshot_data first element")
    print(snapshot_data[0])

    print("current_data first element")
    print(current_data[0])

    # Make sure data hasn't changed
    assert current_data == snapshot_data
