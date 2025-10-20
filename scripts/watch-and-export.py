#!/usr/bin/env python3
"""
Watch for changes in REST API and auto-export OpenAPI schema.

This script monitors the rest_api.py file and automatically exports
the OpenAPI schema when changes are detected.
"""

import json
import sys
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class APIChangeHandler(FileSystemEventHandler):
    """Handler for API file changes."""

    def __init__(self, api_file: Path, output_file: Path):
        self.api_file = api_file
        self.output_file = output_file
        self.last_export = 0

    def on_modified(self, event):
        """Called when a file is modified."""
        if event.src_path == str(self.api_file):
            # Debounce: wait 1 second before exporting
            current_time = time.time()
            if current_time - self.last_export < 1:
                return

            self.last_export = current_time
            print(f"\n🔄 Detected change in {self.api_file.name}")
            self.export_schema()

    def export_schema(self):
        """Export OpenAPI schema."""
        try:
            # Reload the module
            import importlib
            import md2cf.rest_api
            importlib.reload(md2cf.rest_api)

            from md2cf.rest_api import app

            # Get schema
            schema = app.openapi()

            # Write to file
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)

            print(f"✅ OpenAPI schema updated: {self.output_file}")
            print(f"   Version: {schema['info']['version']}")
            print(f"   Endpoints: {len(schema['paths'])}")

        except Exception as e:
            print(f"❌ Error exporting schema: {e}")


def main():
    """Main function."""
    # Paths
    project_root = Path(__file__).parent.parent
    api_file = project_root / "md2cf" / "rest_api.py"
    output_file = project_root / "openapi.json"

    if not api_file.exists():
        print(f"❌ API file not found: {api_file}")
        sys.exit(1)

    print("👀 Watching for changes in REST API...")
    print(f"📁 Monitoring: {api_file}")
    print(f"💾 Output: {output_file}")
    print("\nPress Ctrl+C to stop\n")

    # Initial export
    handler = APIChangeHandler(api_file, output_file)
    handler.export_schema()

    # Setup file watcher
    observer = Observer()
    observer.schedule(handler, str(api_file.parent), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Stopping watcher...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    # Check if watchdog is installed
    try:
        import watchdog
    except ImportError:
        print("❌ watchdog is not installed")
        print("\nInstall with: pip install watchdog")
        sys.exit(1)

    main()
