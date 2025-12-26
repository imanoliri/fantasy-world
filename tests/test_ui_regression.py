import pytest
import json
from pathlib import Path
from playwright.sync_api import Page, expect
import warnings

def test_montreia_ui_tables(page: Page):
    """
    UI Regression test for Montreia tables.
    Opens index.html, navigates to Montreia, opens tables, and verifies content against snapshot.
    """
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent
    index_path = base_dir / "fantasy_worlds" / "index.html"
    index_url = index_path.as_uri()
    snapshot_path = base_dir / "tests" / "data" / "Montreia_map_data_tables.json"
    
    assert snapshot_path.exists(), f"Snapshot file must exist at {snapshot_path}"
    
    # Load snapshot
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)
        
    print(f"Navigating to {index_url}")
    # Navigation
    page.goto(index_url)
    
    # Click Montreia link
    page.click("div.report-card:has-text('Montreia') >> a:has-text('Interactive Map')")
    
    # Wait for load
    # Use a generous timeout for local file loading and map rendering
    try:
        page.wait_for_selector("#toggleStateTable", timeout=60000)
    except Exception as e:
        # Debug info if fails
        print(f"Failed to find #toggleStateTable. Current URL: {page.url}")
        raise e
    
    tables_config = {
        "states": {"button": "#toggleStateTable", "table": "#stateTableContainer table"},
        "burgs": {"button": "#toggleTable", "table": "#burgTableContainer table"},
        "gold_trade": {"button": "#toggleGoldTradeTable", "table": "#goldTradeTableContainer table"},
        "food_trade": {"button": "#toggleFoodTradeTable", "table": "#foodTradeTableContainer table"},
    }
    
    for name, config in tables_config.items():
        print(f"Verifying {name}...")
        
        # Ensure visibility
        if not page.is_visible(config["table"]):
            page.click(config["button"])
            page.wait_for_selector(config["table"], state="visible")
            
        # Scrape
        data = page.eval_on_selector(
            config["table"],
            """
            (table) => {
                const rows = Array.from(table.querySelectorAll('tr'));
                return rows.map(tr => {
                    const cells = Array.from(tr.querySelectorAll('th, td'));
                    return cells.map(td => td.innerText.trim());
                });
            }
            """
        )
        
        # Compare
        expected_data = snapshot[name]
        
        # Debug print if mismatch (pytest will truncate large diffs)
        if data != expected_data:
            print(f"Mismatch in {name}!")
            print(f"Expected: {expected_data[:3]}...")
            print(f"Got: {data[:3]}...")
            
        assert data == expected_data, f"Table {name} mismatch!"

def test_montreia_table_filters(page: Page):
    """
    UI Regression test for Filtering tables.
    Verifies that applying filters (Type=Generic, State=Bukania) correctly filters the Burges table data.
    """
    base_dir = Path(__file__).resolve().parent.parent
    map_path = base_dir / "fantasy_worlds" / "Montreia" / "Montreia_map.html"
    map_url = map_path.as_uri()
    snapshot_path = base_dir / "tests" / "data" / "Montreia_filtered_tables.json"

    print(f"Navigating to {map_url}")
    page.goto(map_url)
    page.wait_for_selector("#toggleStateTable", timeout=60000)

    # Make sure Burgs table is visible
    if not page.is_visible("#burgTableContainer table"):
        page.click("#toggleTable")
        page.wait_for_selector("#burgTableContainer table", state="visible")

    # Helper to scrape current table
    def scrape_table():
        return page.eval_on_selector(
            "#burgTableContainer table",
            """
            (table) => {
                // Get all rows that are NOT hidden (if filtering hides tr)
                // Assuming filtering removes or hides rows.
                // Original script logic likely re-renders the table body or toggles display.
                // Let's scrape visible rows to be safe/accurate.
                const rows = Array.from(table.querySelectorAll('tr'));
                return rows.filter(tr => tr.style.display !== 'none').map(tr => {
                    const cells = Array.from(tr.querySelectorAll('th, td'));
                    return cells.map(td => td.innerText.trim());
                });
            }
            """
        )

    results = {}

    # === Scenario 1: Filter Type = Generic ===
    print("Applying Filter: Type=Generic")
    page.click("button[onclick=\"toggleDropdown('typeDropdown')\"]")
    page.wait_for_timeout(200)
    page.click("#typeCheckboxes input[value='all']") # Uncheck all
    page.wait_for_timeout(200)
    page.click("#typeCheckboxes input[value='Generic']") # Check Generic
    page.wait_for_timeout(500) # Wait for table update

    results["burgs_generic"] = scrape_table()
    
    # Reset Type Filter
    print("Resetting Type Filter")
    page.click("#typeCheckboxes input[value='all']") # Check All
    page.wait_for_timeout(500)
    page.click("button[onclick=\"toggleDropdown('typeDropdown')\"]") # Close dropdown

    # === Scenario 2: Filter State = Bukania ===
    print("Applying Filter: State=Bukania")
    page.click("button[onclick=\"toggleDropdown('stateDropdown')\"]")
    page.wait_for_timeout(200)
    page.click("#stateCheckboxes input[value='all']") # Uncheck all
    page.wait_for_timeout(200)
    page.click("#stateCheckboxes input[value='Bukania']") # Check Bukania
    page.wait_for_timeout(500) # Wait for table update

    results["burgs_bukania"] = scrape_table()

    # Verify or Create Snapshot
    if not snapshot_path.exists():
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
        warnings.warn(f"Created new snapshot at {snapshot_path}. Verify contents manually.")
        return

    # Load Snapshot
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    # Compare
    for key in results:
        # Check simple equality
        if results[key] != snapshot[key]:
            print(f"Mismatch in {key}!")
            # Basic debug
            print(f"Got {len(results[key])} rows, Expected {len(snapshot[key])} rows.")
        assert results[key] == snapshot[key], f"Data mismatch for filter scenario: {key}"
