import pytest
from pathlib import Path
from playwright.sync_api import Page
from PIL import Image, ImageChops
import math
import operator
from functools import reduce

def rmsdiff(im1, im2):
    "Calculate the root-mean-square difference between two images"
    h = ImageChops.difference(im1, im2).histogram()
    return math.sqrt(reduce(operator.add,
        map(lambda h, i: h*(i**2), h, range(256))
    ) / (float(im1.size[0]) * im1.size[1]))

def test_montreia_map_visual(page: Page):
    """
    Visual regression test for the Montreia interactive map.
    Uses Pillow with RMS tolerance to allow for minor rendering differences.
    """
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent
    map_path = base_dir / "fantasy_worlds" / "Montreia" / "Montreia_map.html"
    map_url = map_path.as_uri()

    snapshot_dir = base_dir / "tests" / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / "montreia_map_baseline.png"
    
    current_screenshot_path = snapshot_dir / "montreia_map_current.png"
    diff_path = snapshot_dir / "montreia_map_diff.png"

    assert map_path.exists(), f"Map file must exist at {map_path}"

    print(f"Navigating to {map_url}")
    # Force viewport
    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto(map_url)
    page.wait_for_selector("#toggleStateTable")

    # Stabilize
    page.mouse.move(0, 0)
    page.wait_for_timeout(2000)

    # Take screenshot of the map container only?
    # User previously preferred full page screenshot in their edits.
    # We will use full page to match recent attempts.
    print("Capturing screenshot...")
    page.screenshot(path=str(current_screenshot_path))

    # If baseline doesn't exist, create it
    if not snapshot_path.exists():
        import shutil
        shutil.copy(current_screenshot_path, snapshot_path)
        pytest.fail(f"Snapshot created at {snapshot_path}. Run test again to verify.")

    # Compare
    img_baseline = Image.open(snapshot_path).convert("RGB")
    img_current = Image.open(current_screenshot_path).convert("RGB")

    # Resize checks
    if img_baseline.size != img_current.size:
        pytest.fail(f"Image dimensions differ: Baseline {img_baseline.size} vs Current {img_current.size}")

    # Calculate difference
    diff_score = rmsdiff(img_baseline, img_current)
    print(f"RMS Difference Score: {diff_score}")

    # Tolerance: < 10 is usually invisible/minor noise
    tolerance = 10.0
    
    if diff_score > tolerance:
        diff = ImageChops.difference(img_baseline, img_current)
        diff.save(diff_path)
        pytest.fail(f"Visual mismatch! Score {diff_score} > {tolerance}. Diff saved to {diff_path}")
