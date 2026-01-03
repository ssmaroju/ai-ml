#!/usr/bin/env python
"""
LanceDB CLI for Monitoring System Channel Search

Usage:
    python lancedb_cli.py descriptions "roll rate" --platform Constitution --limit 3
    python lancedb_cli.py dependencies "wind speed" --platform Atlantis
    python lancedb_cli.py coordinates "GPS sensor" --platform Boomvang
    python lancedb_cli.py oandm "calibration procedure" --platform Constitution
    python lancedb_cli.py lineage "Roll Rate" --platform Constitution
    python lancedb_cli.py platforms
"""

import argparse
import warnings
import os
from pathlib import Path

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# Database path
DB_PATH = Path(__file__).parent / "channel_summary_vectordb"

# Lazy-loaded globals
_db = None
_model = None


def get_db():
    """Lazy load LanceDB connection"""
    global _db
    if _db is None:
        import lancedb
        _db = lancedb.connect(str(DB_PATH))
    return _db


def get_model():
    """Lazy load embedding model"""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def search_descriptions(query: str, platform: str = "", device: str = "", limit: int = 5) -> str:
    """Search channel descriptions by semantic similarity."""
    db = get_db()
    model = get_model()

    table = db.open_table("descriptions")
    query_vector = model.encode(query).tolist()

    search = table.search(query_vector)

    filters = []
    if platform:
        filters.append(f"(platform_name = '{platform}' OR platform_alias = '{platform}')")
    if device:
        filters.append(f"device = '{device}'")

    if filters:
        search = search.where(" AND ".join(filters))

    results = search.limit(limit).to_list()

    output = []
    for i, r in enumerate(results[:limit], 1):
        line = f"[{i}] {r.get('platform_name', '')} | {r.get('device', '')} | {r.get('channame', '')}"
        line += f"\n    Units: {r.get('chanunits', '')}"
        line += f"\n    Description: {r.get('description', '')}"
        line += f"\n    System: {r.get('system', '')}"
        output.append(line)

    return "\n\n".join(output) if output else "No results found."


def search_dependencies(query: str, platform: str = "", limit: int = 5) -> str:
    """Search channel dependencies and lineage."""
    db = get_db()
    model = get_model()

    table = db.open_table("dependencies")
    query_vector = model.encode(query).tolist()

    search = table.search(query_vector)

    if platform:
        search = search.where(f"(platform_name = '{platform}' OR platform_alias = '{platform}')")

    results = search.limit(limit).to_list()

    output = []
    for i, r in enumerate(results[:limit], 1):
        node_type = "DERIVED" if r.get("input_count", 0) > 0 else "RAW"
        inputs = r.get("inputs", "")
        outputs = r.get("outputs", "")

        line = f"[{i}] {r.get('platform_name', '')} | {r.get('name', '')} ({node_type})"
        line += f"\n    Device: {r.get('device', '')} | Units: {r.get('units', '')}"
        if inputs:
            line += f"\n    <- Inputs: {inputs}"
        if outputs:
            line += f"\n    -> Outputs: {outputs}"
        output.append(line)

    return "\n\n".join(output) if output else "No results found."


def search_coordinates(query: str, platform: str = "", limit: int = 5) -> str:
    """Search coordinate system information."""
    db = get_db()
    model = get_model()

    table = db.open_table("coordinates")
    query_vector = model.encode(query).tolist()

    search = table.search(query_vector)

    if platform:
        search = search.where(f"(platform_name = '{platform}' OR platform_alias = '{platform}')")

    results = search.limit(limit).to_list()

    output = []
    for i, r in enumerate(results[:limit], 1):
        line = f"[{i}] {r.get('platform_name', '')} | Sensor: {r.get('sensor_name', '')}"
        line += f"\n    Location: X={r.get('x', 'N/A')}, Y={r.get('y', 'N/A')}, Z={r.get('z', 'N/A')}"
        line += f"\n    Coord System: +X={r.get('coord_system_x', '')}, +Y={r.get('coord_system_y', '')}, +Z={r.get('coord_system_z', '')}"
        line += f"\n    Platform Heading: {r.get('heading_deg', 'N/A')} deg from True North"
        line += f"\n    Lat/Lon: {r.get('latitude', '')}, {r.get('longitude', '')}"
        output.append(line)

    return "\n\n".join(output) if output else "No results found."


def search_oandm(query: str, platform: str = "", limit: int = 5) -> str:
    """Search O&M manual content."""
    db = get_db()
    model = get_model()

    table = db.open_table("oandm_manuals")
    query_vector = model.encode(query).tolist()

    search = table.search(query_vector)

    if platform:
        search = search.where(f"platform_name = '{platform}'")

    results = search.limit(limit).to_list()

    output = []
    for i, r in enumerate(results[:limit], 1):
        content = r.get("content", "")[:500]
        line = f"[{i}] {r.get('platform_name', '')} | {r.get('document_name', '')}"
        line += f"\n    (Chunk {r.get('chunk_id', 0)+1} of {r.get('total_chunks', '?')})"
        line += f"\n    Content: {content}..."
        output.append(line)

    return "\n\n".join(output) if output else "No results found."


def get_channel_lineage(channel_name: str, platform: str) -> str:
    """Get complete lineage for a specific channel."""
    db = get_db()
    model = get_model()

    table = db.open_table("dependencies")
    query_vector = model.encode(f"{channel_name} {platform}").tolist()

    results = table.search(query_vector).where(
        f"(platform_name = '{platform}' OR platform_alias = '{platform}')"
    ).limit(10).to_list()

    if not results:
        return f"No channel matching '{channel_name}' found for platform '{platform}'."

    # Find best match
    best_match = None
    for r in results:
        if channel_name.lower() in r.get("name", "").lower():
            best_match = r
            break

    if not best_match:
        best_match = results[0]

    # Format detailed lineage
    output = f"Channel: {best_match.get('name', 'Unknown')}"
    output += f"\nPlatform: {best_match.get('platform_name', '')} ({best_match.get('platform_alias', '')})"
    output += f"\nSystem: {best_match.get('system', '')}"
    output += f"\nDevice: {best_match.get('device', '')}"
    output += f"\nUnits: {best_match.get('units', '')}"
    output += f"\nCategory: {best_match.get('category', '')}"

    is_derived = best_match.get("input_count", 0) > 0
    output += f"\nType: {'DERIVED' if is_derived else 'RAW/MEASURED'}"

    inputs = best_match.get("inputs", "")
    outputs = best_match.get("outputs", "")

    if inputs:
        output += f"\n\nUpstream Inputs (this channel is derived from):"
        for inp in inputs.split(","):
            output += f"\n  <- {inp.strip()}"
    else:
        output += "\n\nUpstream Inputs: None (raw sensor data)"

    if outputs:
        output += f"\n\nDownstream Outputs (channels derived from this):"
        for out in outputs.split(","):
            output += f"\n  -> {out.strip()}"
    else:
        output += "\n\nDownstream Outputs: None (terminal channel)"

    return output


def list_platforms() -> str:
    """List all available platforms."""
    db = get_db()

    platforms = {}

    for table_name in ["descriptions", "dependencies", "coordinates", "oandm_manuals"]:
        try:
            table = db.open_table(table_name)
            df = table.to_pandas()
            for p in df["platform_name"].unique():
                if p:
                    if p not in platforms:
                        platforms[p] = []
                    platforms[p].append(table_name[:4])
        except Exception:
            continue

    output = "Available Platforms:\n" + "-" * 50
    for p in sorted(platforms.keys()):
        tables = ", ".join(platforms[p])
        output += f"\n{p}: [{tables}]"

    return output


def main():
    parser = argparse.ArgumentParser(description="LanceDB Channel Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Search commands")

    # descriptions
    desc_parser = subparsers.add_parser("descriptions", help="Search channel descriptions")
    desc_parser.add_argument("query", help="Search query")
    desc_parser.add_argument("--platform", "-p", default="", help="Platform filter")
    desc_parser.add_argument("--device", "-d", default="", help="Device filter")
    desc_parser.add_argument("--limit", "-n", type=int, default=5, help="Max results")

    # dependencies
    dep_parser = subparsers.add_parser("dependencies", help="Search channel dependencies")
    dep_parser.add_argument("query", help="Search query")
    dep_parser.add_argument("--platform", "-p", default="", help="Platform filter")
    dep_parser.add_argument("--limit", "-n", type=int, default=5, help="Max results")

    # coordinates
    coord_parser = subparsers.add_parser("coordinates", help="Search coordinate systems")
    coord_parser.add_argument("query", help="Search query")
    coord_parser.add_argument("--platform", "-p", default="", help="Platform filter")
    coord_parser.add_argument("--limit", "-n", type=int, default=5, help="Max results")

    # oandm
    oandm_parser = subparsers.add_parser("oandm", help="Search O&M manuals")
    oandm_parser.add_argument("query", help="Search query")
    oandm_parser.add_argument("--platform", "-p", default="", help="Platform filter")
    oandm_parser.add_argument("--limit", "-n", type=int, default=5, help="Max results")

    # lineage
    lineage_parser = subparsers.add_parser("lineage", help="Get channel lineage")
    lineage_parser.add_argument("channel", help="Channel name")
    lineage_parser.add_argument("--platform", "-p", required=True, help="Platform name")

    # platforms
    subparsers.add_parser("platforms", help="List available platforms")

    args = parser.parse_args()

    if args.command == "descriptions":
        print(search_descriptions(args.query, args.platform, args.device, args.limit))
    elif args.command == "dependencies":
        print(search_dependencies(args.query, args.platform, args.limit))
    elif args.command == "coordinates":
        print(search_coordinates(args.query, args.platform, args.limit))
    elif args.command == "oandm":
        print(search_oandm(args.query, args.platform, args.limit))
    elif args.command == "lineage":
        print(get_channel_lineage(args.channel, args.platform))
    elif args.command == "platforms":
        print(list_platforms())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
