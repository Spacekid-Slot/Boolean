#!/usr/bin/env python3
"""
Trigger Claude Update

Run this to manually trigger a sync of Claude's latest updates.
"""

import json
from pathlib import Path

def trigger_update():
    """Trigger an update from Claude."""
    script_dir = Path(__file__).parent.absolute()
    
    # Create an updates file that the watcher will detect
    updates = {
        "script2_web_scraping.py": "# Updated by trigger",
        "fix_excel_and_linkedin.py": "# Updated by trigger"
    }
    
    updates_file = script_dir / "claude_updates.json"
    with open(updates_file, 'w') as f:
        json.dump(updates, f)
    
    print("✅ Update triggered - real-time sync will apply changes")

if __name__ == "__main__":
    trigger_update()
