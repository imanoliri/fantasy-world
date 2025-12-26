import pytest
import json
from pathlib import Path
from playwright.sync_api import Page, expect

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
