# Skills Layer - Question Classification & Routing

This layer classifies user questions and routes to the appropriate skill.

## Prerequisites

Before using any skill:
1. Access mode validation must be complete (see parent `.claude/CLAUDE.md`)
2. Platform name must be resolved to original name (for internal search)
3. Output transformation must be applied after skill returns (for alias mode)

## Question Classification

### Channel Description
**Skill**: `channel-description.md`

**Triggers**:
- "What is [channel]?"
- "Define [channel]"
- "What does [channel] measure?"
- "What are the units for [channel]?"
- "Describe [channel]"

**Data Sources**: descriptions → dependencies (fallback) → cross-platform → web

---

### Channel Dependency / Lineage
**Skill**: `channel-dependency.md`

**Triggers**:
- "How is [channel] derived?"
- "What feeds [channel]?"
- "What is the lineage of [channel]?"
- "Is [channel] raw or processed?"
- "What channels depend on [channel]?"
- "Upstream/downstream of [channel]"

**Data Sources**: dependencies, lineage query

---

### Coordinate System
**Skill**: `coordinate-system.md`

**Triggers**:
- "What is the coordinate system for [platform]?"
- "Where is [sensor] located?"
- "+X direction on [platform]"
- "Platform heading"
- "Sensor orientation"

**Data Sources**: coordinates

---

### O&M Manual Search
**Skill**: `oandm-search.md`

**Triggers**:
- "Calibration procedure for..."
- "Maintenance schedule for..."
- "How do I troubleshoot..."
- "Operating procedure for..."
- "What does the manual say about..."

**Data Sources**: oandm_manuals

---

### Channel Resolution (Ambiguous)
**Skill**: `channel-resolver.md`

**Triggers**:
- Ambiguous channel reference
- Multiple possible matches
- User asks to clarify between channels

**Data Sources**: all tables

---

### General / Orchestrated Query
**Skill**: `monitoring-assistant.md`

**Triggers**:
- Complex multi-part questions
- Questions spanning multiple categories
- When unsure of classification

**Data Sources**: all tables + domain knowledge

## Routing Decision Tree

```
User Question
      │
      ├─── Contains "what is" / "define" / "describe"
      │         └──► channel-description.md
      │
      ├─── Contains "derived" / "lineage" / "feeds" / "depends"
      │         └──► channel-dependency.md
      │
      ├─── Contains "coordinate" / "orientation" / "+X" / "heading"
      │         └──► coordinate-system.md
      │
      ├─── Contains "calibration" / "maintenance" / "procedure" / "manual"
      │         └──► oandm-search.md
      │
      ├─── Ambiguous channel reference
      │         └──► channel-resolver.md
      │
      └─── Complex / Multi-part / Unclear
                └──► monitoring-assistant.md
```

## Search Workflow (All Skills)

```
1. SEARCH LOCAL (platform-specific)
   │
   ├─► lancedb_cli.py [table] "[query]" --platform "[platform]"
   │
   └─► If results found → format and return

2. IF NOT FOUND → SEARCH CROSS-PLATFORM
   │
   ├─► lancedb_cli.py [table] "[query]" --limit 5
   │
   └─► If results found → "No data for [platform], generic from [other]: ..."

3. IF STILL NOT FOUND → SEARCH WEB
   │
   └─► Search for industry-standard definition
       └─► "No local data. Generic definition: ..."
```

## Query Transformation

Before searching, transform queries based on platform type (see `data/platform_domain.json`):

| User Query | Platform Type | Search Query |
|------------|---------------|--------------|
| "Northings" | Spar | "Spar Northings" |
| "Northings" | TLP/Semi | "PQ Northings" |
| "Northings" | FPSO | "Grid Northings" |
| "Roll" | Any | "Spar Roll" or "Roll" (not "Roll Rate") |
| "Wind Speed" | Any | "Best Wind Speed" |

## CLI Commands Reference

```bash
# Descriptions
uv run --with lancedb --with sentence-transformers --with pandas python lancedb_cli.py descriptions "<query>" --platform "<platform>" --limit N

# Dependencies
uv run --with lancedb --with sentence-transformers --with pandas python lancedb_cli.py dependencies "<query>" --platform "<platform>" --limit N

# Lineage (specific channel)
uv run --with lancedb --with sentence-transformers --with pandas python lancedb_cli.py lineage "<channel>" --platform "<platform>"

# Coordinates
uv run --with lancedb --with sentence-transformers --with pandas python lancedb_cli.py coordinates "<query>" --platform "<platform>" --limit N

# O&M Manuals
uv run --with lancedb --with sentence-transformers --with pandas python lancedb_cli.py oandm "<query>" --platform "<platform>" --limit N

# List platforms
uv run --with lancedb --with sentence-transformers --with pandas python lancedb_cli.py platforms
```
