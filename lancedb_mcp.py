"""
LanceDB MCP Server for Monitoring System Assistant

Provides vector search tools for:
- Channel descriptions
- Channel dependencies/lineage
- Platform coordinate systems
- O&M manual content
"""

import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("LanceDB Channel Search")

# Database path (relative to this file)
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


def format_results(results: list, fields: list, max_results: int = 10) -> str:
    """Format search results as readable text"""
    if not results:
        return "No results found."

    output = []
    for i, r in enumerate(results[:max_results], 1):
        parts = [f"[{i}]"]
        for field in fields:
            if field in r and r[field]:
                parts.append(f"{field}: {r[field]}")
        output.append(" | ".join(parts))

    return "\n".join(output)


@mcp.tool()
def search_descriptions(query: str, platform: str = "", device: str = "", limit: int = 5) -> str:
    """
    Search channel descriptions by semantic similarity.

    Args:
        query: Natural language search query (e.g., "roll rate", "wind speed")
        platform: Optional platform name filter (e.g., "Constitution", "Atlantis")
        device: Optional device filter (e.g., "6DOF", "GPS")
        limit: Maximum results to return (default 5)

    Returns:
        Matching channel descriptions with platform, device, name, units, and description
    """
    db = get_db()
    model = get_model()

    table = db.open_table("descriptions")
    query_vector = model.encode(query).tolist()

    # Build search
    search = table.search(query_vector)

    # Apply filters
    filters = []
    if platform:
        filters.append(f"(platform_name = '{platform}' OR platform_alias = '{platform}')")
    if device:
        filters.append(f"device = '{device}'")

    if filters:
        search = search.where(" AND ".join(filters))

    results = search.limit(limit).to_list()

    fields = ["platform_name", "system", "device", "channame", "chanunits", "description"]
    return format_results(results, fields)


@mcp.tool()
def search_dependencies(query: str, platform: str = "", limit: int = 5) -> str:
    """
    Search channel dependencies and lineage information.

    Args:
        query: Search query (e.g., "wind speed", "derived channels")
        platform: Optional platform name filter
        limit: Maximum results to return

    Returns:
        Matching channels with their inputs (upstream) and outputs (downstream) connections
    """
    db = get_db()
    model = get_model()

    table = db.open_table("dependencies")
    query_vector = model.encode(query).tolist()

    search = table.search(query_vector)

    if platform:
        search = search.where(f"(platform_name = '{platform}' OR platform_alias = '{platform}')")

    results = search.limit(limit).to_list()

    # Format with lineage info
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


@mcp.tool()
def search_coordinates(query: str, platform: str = "", limit: int = 5) -> str:
    """
    Search platform and sensor coordinate system information.

    Args:
        query: Search query (e.g., "GPS location", "6DOF sensor")
        platform: Optional platform name filter
        limit: Maximum results to return

    Returns:
        Coordinate system info including orientation (+X, +Y, +Z) and sensor locations
    """
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
        line += f"\n    Platform Heading: {r.get('heading_deg', 'N/A')}° from True North"
        line += f"\n    Lat/Lon: {r.get('latitude', '')}, {r.get('longitude', '')}"
        output.append(line)

    return "\n\n".join(output) if output else "No results found."


@mcp.tool()
def search_oandm(query: str, platform: str = "", limit: int = 5) -> str:
    """
    Search Operations & Maintenance manual content.

    Args:
        query: Search query (e.g., "calibration procedure", "maintenance schedule")
        platform: Optional platform name filter
        limit: Maximum results to return

    Returns:
        Relevant excerpts from O&M manuals with source document info
    """
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
        content = r.get("content", "")[:500]  # Truncate for readability
        line = f"[{i}] {r.get('platform_name', '')} | {r.get('document_name', '')}"
        line += f"\n    (Chunk {r.get('chunk_id', 0)+1} of {r.get('total_chunks', '?')})"
        line += f"\n    Content: {content}..."
        output.append(line)

    return "\n\n".join(output) if output else "No results found."


@mcp.tool()
def get_channel_lineage(channel_name: str, platform: str) -> str:
    """
    Get the complete lineage (upstream and downstream) for a specific channel.

    Args:
        channel_name: Name of the channel to look up
        platform: Platform name (required for specificity)

    Returns:
        Channel details with all upstream (input) and downstream (output) connections
    """
    db = get_db()
    model = get_model()

    table = db.open_table("dependencies")

    # Search for the specific channel
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
        best_match = results[0]  # Use closest semantic match

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


@mcp.tool()
def list_platforms() -> str:
    """
    List all available platforms in the database.

    Returns:
        List of platform names with data availability in each table
    """
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
                    platforms[p].append(table_name[:4])  # Abbreviate
        except:
            continue

    output = "Available Platforms:\n" + "-" * 50
    for p in sorted(platforms.keys()):
        tables = ", ".join(platforms[p])
        output += f"\n{p}: [{tables}]"

    return output


if __name__ == "__main__":
    mcp.run()
