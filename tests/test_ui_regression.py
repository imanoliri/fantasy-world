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
    Verifies that applying filters (Type=Generic, State=Bukania) correctly filters ALL tables.
    Order: States, Burgs, Food Trade, Gold Trade.
    """
    base_dir = Path(__file__).resolve().parent.parent
    map_path = base_dir / "fantasy_worlds" / "Montreia" / "Montreia_map.html"
    map_url = map_path.as_uri()
    snapshot_path = base_dir / "tests" / "data" / "Montreia_filtered_tables.json"

    print(f"Navigating to {map_url}")
    page.goto(map_url)
    page.wait_for_selector("#toggleStateTable", timeout=60000)

    tables_config = {
        "states": {"button": "#toggleStateTable", "table": "#stateTableContainer table"},
        "burgs": {"button": "#toggleTable", "table": "#burgTableContainer table"},
        "food_trade": {"button": "#toggleFoodTradeTable", "table": "#foodTradeTableContainer table"},
        "gold_trade": {"button": "#toggleGoldTradeTable", "table": "#goldTradeTableContainer table"},
    }
    tables_order = ["states", "burgs", "food_trade", "gold_trade"]

    # Helper to scrape visible rows of a table
    def scrape_visible(table_selector):
        return page.eval_on_selector(
            table_selector,
            """
            (table) => {
                const rows = Array.from(table.querySelectorAll('tr'));
                // Filter rows that are display:none
                return rows.filter(tr => tr.style.display !== 'none').map(tr => {
                    const cells = Array.from(tr.querySelectorAll('th, td'));
                    return cells.map(td => td.innerText.trim());
                });
            }
            """
        )

    results = {}

    def capture_scenario(scenario_prefix):
        for name in tables_order:
            config = tables_config[name]
            print(f"Scraping {name} for {scenario_prefix}...")
            # Ensure visible
            if not page.is_visible(config["table"]):
                page.click(config["button"])
                page.wait_for_selector(config["table"], state="visible")
            
            # Scrape
            key = f"{scenario_prefix}_{name}"
            results[key] = scrape_visible(config["table"])

    # === Scenario 1: Filter Type = Generic ===
    print("Applying Filter: Type=Generic")
    page.click("button[onclick=\"toggleDropdown('typeDropdown')\"]")
    page.wait_for_timeout(200)
    page.click("#typeCheckboxes input[value='all']") # Uncheck all
    page.wait_for_timeout(200)
    page.click("#typeCheckboxes input[value='Generic']") # Check Generic
    page.wait_for_timeout(500) # Wait for table update

    capture_scenario("generic")
    
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

    capture_scenario("bukania")

    # Verify or Create Snapshot
    if not snapshot_path.exists():
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
        warnings.warn(f"Created new snapshot at {snapshot_path}. Verify contents manually.")
        return

    # Load Snapshot
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    # Automatic update logic for compatibility
    keys_mismatch = set(results.keys()) - set(snapshot.keys())
    if keys_mismatch:
         print(f"New keys found: {keys_mismatch}. Updating snapshot.")
         snapshot.update(results)
         with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=4)
         warnings.warn(f"Updated snapshot at {snapshot_path} with new keys. Verify manually.")
         
    # Compare
    for key in results:
        if key not in snapshot:
            continue
        if results[key] != snapshot[key]:
            print(f"Mismatch in {key}!")
            print(f"Got {len(results[key])} rows, Expected {len(snapshot[key])} rows.")
        assert results[key] == snapshot[key], f"Data mismatch for {key}"

def test_montreia_search_data(page: Page):
    """
    UI Regression test for Search.
    Verifies that searching for 'ia' correctly filters ALL tables.
    Order: States, Burgs, Food Trade, Gold Trade.
    """
    base_dir = Path(__file__).resolve().parent.parent
    map_path = base_dir / "fantasy_worlds" / "Montreia" / "Montreia_map.html"
    map_url = map_path.as_uri()
    snapshot_path = base_dir / "tests" / "data" / "Montreia_search_tables.json"

    print(f"Navigating to {map_url} (Search Data Test)")
    page.goto(map_url)
    page.wait_for_selector("#toggleStateTable", timeout=60000)

    tables_config = {
        "states": {"button": "#toggleStateTable", "table": "#stateTableContainer table"},
        "burgs": {"button": "#toggleTable", "table": "#burgTableContainer table"},
        "food_trade": {"button": "#toggleFoodTradeTable", "table": "#foodTradeTableContainer table"},
        "gold_trade": {"button": "#toggleGoldTradeTable", "table": "#goldTradeTableContainer table"},
    }
    tables_order = ["states", "burgs", "food_trade", "gold_trade"]

    # Helper to scrape visible rows
    def scrape_visible(table_selector):
        return page.eval_on_selector(
            table_selector,
            """
            (table) => {
                const rows = Array.from(table.querySelectorAll('tr'));
                // Filter rows that are display:none
                return rows.filter(tr => tr.style.display !== 'none').map(tr => {
                    const cells = Array.from(tr.querySelectorAll('th, td'));
                    return cells.map(td => td.innerText.trim());
                });
            }
            """
        )

    results = {}

    # === Scenario: Search "ia" ===
    print("Typing 'ia' into search box...")
    page.type("#searchInput", "ia")
    page.wait_for_timeout(1000) # Wait for debounce/filter

    for name in tables_order:
        config = tables_config[name]
        print(f"Scraping {name} for search='ia'...")
        # Ensure visible
        if not page.is_visible(config["table"]):
            page.click(config["button"])
            page.wait_for_selector(config["table"], state="visible")
        
        # Scrape
        results[name] = scrape_visible(config["table"])

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
        if results[key] != snapshot[key]:
            print(f"Mismatch in {key}!")
            print(f"Got {len(results[key])} rows, Expected {len(snapshot[key])} rows.")
        assert results[key] == snapshot[key], f"Data mismatch for {key}"

def test_montreia_sorting_data(page: Page):
    """
    UI Regression test for Table Sorting.
    Verifies that clicking headers sorts the data.
    Focus on Burgs table for simplicity and "Name" and "Population" (if available).
    """
    base_dir = Path(__file__).resolve().parent.parent
    map_path = base_dir / "fantasy_worlds" / "Montreia" / "Montreia_map.html"
    map_url = map_path.as_uri()
    snapshot_path = base_dir / "tests" / "data" / "Montreia_sorting_tables.json"

    print(f"Navigating to {map_url} (Sorting Test)")
    page.goto(map_url)
    page.wait_for_selector("#toggleStateTable", timeout=60000)

    # Ensure Burgs table visible
    if not page.is_visible("#burgTableContainer table"):
        page.click("#toggleTable")
        page.wait_for_selector("#burgTableContainer table", state="visible")

    def scrape_table():
         return page.eval_on_selector(
            "#burgTableContainer table",
            """
            (table) => {
                const rows = Array.from(table.querySelectorAll('tr'));
                // Return visible rows. The header row is usually visible. 
                // We mainly care about the order of data rows.
                return rows.filter(tr => tr.style.display !== 'none').map(tr => {
                    const cells = Array.from(tr.querySelectorAll('th, td'));
                    return cells.map(td => td.innerText.trim());
                });
            }
            """
        )

    results = {}

    # === Sort by Name (Ascending?) ===
    # Assuming first click sorts Ascending, second Descending, or vice versa depending on default.
    # Usually first column header is Name.
    print("Clicking First Column Header (Burg/Name)...")
    # Click the TH inside the table. Assuming index 0.
    page.click("#burgTableContainer table th:nth-child(1)")
    page.wait_for_timeout(500)
    results["burgs_sort_name_1"] = scrape_table()

    # === Sort by Name (Descending?) ===
    print("Clicking First Column Header Again...")
    page.click("#burgTableContainer table th:nth-child(1)")
    page.wait_for_timeout(500)
    results["burgs_sort_name_2"] = scrape_table()

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
        if results[key] != snapshot[key]:
            print(f"Mismatch in {key}!")
            # Print first 3 rows
            print(f"Got: {results[key][1:4]}")
            print(f"Exp: {snapshot[key][1:4]}")
        assert results[key] == snapshot[key], f"Sorting mismatch for {key}"
