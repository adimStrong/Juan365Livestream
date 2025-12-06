"""
Juan365 Report Local Server
Simple HTTP server to preview reports at localhost:8080
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Configuration
PORT = 8080
OUTPUT_DIR = Path(__file__).parent / "output"


def get_latest_report():
    """Find the most recent HTML report"""
    # Prefer LATEST file
    latest = OUTPUT_DIR / "Juan365_Report_LATEST.html"
    if latest.exists():
        return latest.name

    # Then any report file
    reports = list(OUTPUT_DIR.glob("Juan365_Report_*.html"))
    if reports:
        reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return reports[0].name

    # Fallback to any HTML
    reports = list(OUTPUT_DIR.glob("*.html"))
    if not reports:
        return None
    reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return reports[0].name


def main():
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)
    os.chdir(OUTPUT_DIR)

    latest_report = get_latest_report()

    print("=" * 60)
    print("JUAN365 REPORT LOCAL SERVER")
    print("=" * 60)
    print(f"Serving from: {OUTPUT_DIR}")
    print(f"Port: {PORT}")
    print(f"URL: http://localhost:{PORT}")
    if latest_report:
        print(f"Latest report: {latest_report}")
        print(f"Direct link: http://localhost:{PORT}/{latest_report}")
    else:
        print("[WARNING] No reports found. Run generate_report.py first.")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    # Create handler
    handler = http.server.SimpleHTTPRequestHandler
    handler.extensions_map.update({
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
    })

    with socketserver.TCPServer(("", PORT), handler) as httpd:
        # Open browser to the latest report
        if latest_report:
            url = f"http://localhost:{PORT}/{latest_report}"
        else:
            url = f"http://localhost:{PORT}"

        webbrowser.open(url)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[INFO] Server stopped.")


if __name__ == "__main__":
    main()
