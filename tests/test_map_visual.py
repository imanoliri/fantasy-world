import pytest
import time
from pathlib import Path
from playwright.sync_api import Page
from PIL import Image, ImageChops
import math
import operator
from functools import reduce
import warnings

def rmsdiff(im1, im2):
    "Calculate the root-mean-square difference between two images"
    if im1.size != im2.size or im1.mode != im2.mode:
        return 9999.9
    h = ImageChops.difference(im1, im2).histogram()
    return math.sqrt(reduce(operator.add,
        map(lambda h, i: h*(i**2), h, range(256))
    ) / (float(im1.size[0]) * im1.size[1]))

def verify_visual_state(page: Page, snapshot_name: str, tolerance: float = 1.0, expect_fail: bool = False, suffix_str: str = None):
    """
    Helper to take a screenshot and compare it with baseline using PIL RMS.
    
    Args:
        page: Playwright page object.
        snapshot_name: Base name for snapshot files.
        tolerance: RMS difference tolerance (default 1.0).
        expect_fail: If True, asserts that the comparison FAILS (RMS > tolerance).
        suffix_str: suffix to add to the snapshot name.
    """
    base_dir = Path(__file__).resolve().parent.parent
    snapshot_dir = base_dir / "tests" / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    #Add suffix if provided
    if not suffix_str:
        suffix_str = ""
    snapshot_path = snapshot_dir / f"{snapshot_name}_baseline{suffix_str}.png"

    current_path = snapshot_dir / f"{snapshot_name}_current{suffix_str}.png"
    diff_path = snapshot_dir / f"{snapshot_name}_diff{suffix_str}.png"

    # Ensure consistent viewport before screenshot
    page.set_viewport_size({"width": 1280, "height": 720})

    print(f"Capturing snapshot for: {snapshot_name}")
    page.screenshot(path=str(current_path))

    # Create baseline if missing (Only if NOT expecting fail)
    if not snapshot_path.exists():
        if expect_fail:
            pytest.fail(f"Expected failure baseline {snapshot_path} does not exist. Cannot run negative test.")
        
        import shutil
        shutil.copy(current_path, snapshot_path)
        warnings.warn(f"Snapshot created at {snapshot_path}. Run test again to verify.")
        return

    img_baseline = Image.open(snapshot_path).convert("RGB")
    img_current = Image.open(current_path).convert("RGB")

    if img_baseline.size != img_current.size:
        pytest.fail(f"Image dimensions differ: Baseline {img_baseline.size} vs Current {img_current.size}")

    diff_score = rmsdiff(img_baseline, img_current)
    print(f"RMS Difference Score ({snapshot_name} vs {snapshot_path.name}): {diff_score}")

    if expect_fail:
        if diff_score <= tolerance:
            ImageChops.difference(img_baseline, img_current).save(diff_path)
            pytest.fail(f"Negative Test unsuccesful! Expected mismatch > {tolerance}, but got {diff_score}. Images match too closely.")
        return

    if diff_score > tolerance:
        ImageChops.difference(img_baseline, img_current).save(diff_path)
        pytest.fail(f"Visual mismatch for {snapshot_name}! Score {diff_score} > {tolerance}. Diff saved to {diff_path}")

def test_montreia_map_visual(page: Page):
    """
    Initial state visual regression test.
    """
    base_dir = Path(__file__).resolve().parent.parent
    map_path = base_dir / "fantasy_worlds" / "Montreia" / "Montreia_map.html"
    map_url = map_path.as_uri()

    print(f"Navigating to {map_url}")
    page.goto(map_url)
    page.wait_for_selector("#toggleStateTable")

    # Stabilize
    page.mouse.move(0, 0)
    page.wait_for_timeout(2000)

    verify_visual_state(page, "montreia_map")

def test_montreia_visual_fail_check(page: Page):
    """
    Negative Test: verify that the system correctly identifies a mismatch.
    Compares current map state against 'montreia_map_baseline__FALSE.png'.
    """
    base_dir = Path(__file__).resolve().parent.parent
    map_path = base_dir / "fantasy_worlds" / "Montreia" / "Montreia_map.html"
    map_url = map_path.as_uri()

    print(f"Navigating to {map_url} (Negative Test)")
    page.goto(map_url)
    page.wait_for_selector("#toggleStateTable")
    
    # Stabilize
    page.mouse.move(0, 0)
    page.wait_for_timeout(2000)

    verify_visual_state(
        page, 
        "montreia_map", 
        suffix_str="__FALSE",
        expect_fail=True
    )

def test_montreia_map_buttons_sequence(page: Page):
    """
    Sequential visual test:
    1. Initial Load
    2. Click Show Map (#toggleMap)
    3. Click Food Trade (#toggleFoodTrades)
    4. Click Gold Trade (#toggleGoldTrades)
    5. Click Highlight Capitals (#toggleCapitals)
    """
    base_dir = Path(__file__).resolve().parent.parent
    map_path = base_dir / "fantasy_worlds" / "Montreia" / "Montreia_map.html"
    map_url = map_path.as_uri()

    print(f"Navigating to {map_url} (Sequence Test)")
    page.goto(map_url)
    page.wait_for_selector("#toggleStateTable")

    # Stabilize
    page.mouse.move(0, 0)
    page.wait_for_timeout(1000)

    # 1. Toggle Map
    print("Clicking Toggle Map...")
    page.click("#toggleMap")
    page.wait_for_timeout(500)
    verify_visual_state(page, "montreia_seq_1_map_click")

    # 2. Toggle Food Trade
    print("Clicking Toggle Food Trade...")
    page.click("#toggleFoodTrades")
    page.wait_for_timeout(500)
    verify_visual_state(page, "montreia_seq_2_food_click")

    # 3. Toggle Gold Trade
    print("Clicking Toggle Gold Trade...")
    page.click("#toggleGoldTrades")
    page.wait_for_timeout(500)
    verify_visual_state(page, "montreia_seq_3_gold_click")

    # 4. Toggle Capitals
    print("Clicking Toggle Capitals...")
    page.click("#toggleCapitals")
    page.wait_for_timeout(500)
    verify_visual_state(page, "montreia_seq_4_capitals_click")

def test_montreia_map_filters(page: Page):
    """
    Filter Interaction visual test:
    1. Show Map
    2. Filter Types: Uncheck All, Check Generic
    3. Reset Types: Check All
    4. Filter States: Uncheck All, Check Bukania
    """
    base_dir = Path(__file__).resolve().parent.parent
    map_path = base_dir / "fantasy_worlds" / "Montreia" / "Montreia_map.html"
    map_url = map_path.as_uri()

    print(f"Navigating to {map_url} (Filter Test)")
    page.goto(map_url)
    page.wait_for_selector("#toggleStateTable")

    # Stabilize
    page.mouse.move(0, 0)
    page.wait_for_timeout(1000)

    # Hide Map
    print("Clicking Show Map button...")
    page.click("#toggleMap")
    page.wait_for_timeout(500)

    # Filter Types
    print("Opening Filter Types...")
    page.click("button[onclick=\"toggleDropdown('typeDropdown')\"]")
    page.wait_for_timeout(200)

    print("Unselecting All Types...")
    page.click("#typeCheckboxes input[value='all']")
    page.wait_for_timeout(200)

    print("Selecting Generic...")
    page.click("#typeCheckboxes input[value='Generic']")
    page.wait_for_timeout(500)
    
    verify_visual_state(page, "montreia_filter_type_generic")

    # Select all types back & close dropdown
    print("Reselecting All Types...")
    page.click("#typeCheckboxes input[value='all']")
    page.wait_for_timeout(500)
    
    page.click("button[onclick=\"toggleDropdown('typeDropdown')\"]") 
    page.wait_for_timeout(200)

    # Filter States
    print("Opening Filter States...")
    page.click("button[onclick=\"toggleDropdown('stateDropdown')\"]")
    page.wait_for_timeout(200)

    print("Unselecting All States...")
    page.click("#stateCheckboxes input[value='all']")
    page.wait_for_timeout(200)

    print("Selecting Bukania...")
    page.click("#stateCheckboxes input[value='Bukania']")
    page.wait_for_timeout(500)

    verify_visual_state(page, "montreia_filter_state_bukania")
