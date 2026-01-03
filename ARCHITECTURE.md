# Monitoring System Assistant - Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER QUERY                                        │
│                    "What is Northings on Constitution?"                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ACCESS CONTROL LAYER                                │
│                        (.claude/CLAUDE.md)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Determine current MODE (Admin/Actual/Alias)                             │
│  2. Validate platform name against mode rules                               │
│  3. Transform names if needed (alias ↔ actual)                              │
│  4. Route to appropriate skill                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │  ADMIN MODE  │  │  ACTUAL MODE │  │  ALIAS MODE  │
         │              │  │              │  │              │
         │ • Use either │  │ • Only actual│  │ • Only alias │
         │   name       │  │   names work │  │   names work │
         │ • Show both  │  │ • Show actual│  │ • Show alias │
         │   in output  │  │   in output  │  │   in output  │
         └──────────────┘  └──────────────┘  └──────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SKILL ROUTER                                      │
│                      (.claude/skills/CLAUDE.md)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Question Type         │  Skill                  │  Data Source             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  "What is X?"          │  channel-description    │  descriptions, deps      │
│  "How is X derived?"   │  channel-dependency     │  dependencies            │
│  "Coordinate system?"  │  coordinate-system      │  coordinates             │
│  "Calibration/maint?"  │  oandm-search           │  oandm_manuals           │
│  "Ambiguous channel"   │  channel-resolver       │  all tables              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DOMAIN KNOWLEDGE                                   │
│                      (data/platform_domain.json)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Platform types (Spar, TLP, Semi, FPSO)                                   │
│  • Query transformation rules (Northings → Spar Northings)                  │
│  • Terminology definitions                                                  │
│  • Channel priority rules                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SEARCH WORKFLOW                                   │
│                      (lancedb_cli.py)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Search LOCAL (platform-specific)                                        │
│     └─ descriptions → dependencies → coordinates → oandm                    │
│  2. If not found, search CROSS-PLATFORM                                     │
│     └─ Same channel type on other platforms                                 │
│  3. If still not found, search WEB                                          │
│     └─ Industry-standard definitions                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RESPONSE FORMATTER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Apply name masking based on MODE                                         │
│  • Format channel definition                                                │
│  • Add source citations                                                     │
│  • Add domain context                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
project_root/
├── CLAUDE.md                         # Project overview (existing)
│
├── .claude/
│   ├── CLAUDE.md                     # ACCESS CONTROL & ORCHESTRATION
│   │   └─ Mode management (Admin/Actual/Alias)
│   │   └─ Name validation & transformation
│   │   └─ Security rules
│   │
│   ├── settings.local.json           # Tool permissions
│   │
│   └── skills/
│       ├── CLAUDE.md                 # SKILL ROUTING
│       │   └─ Question classification
│       │   └─ Skill selection logic
│       │
│       ├── channel-description.md    # "What is X?"
│       ├── channel-dependency.md     # "How is X derived?"
│       ├── channel-resolver.md       # Ambiguous references
│       ├── coordinate-system.md      # Coordinate systems
│       ├── oandm-search.md           # O&M manual search
│       └── monitoring-assistant.md   # Full orchestrator (legacy)
│
├── data/
│   ├── platform_domain.json          # DOMAIN KNOWLEDGE
│   │   └─ Platform types
│   │   └─ Terminology
│   │   └─ Query transformation rules
│   │
│   ├── platform_names.json           # NAME MAPPING
│   │   └─ actual ↔ alias mapping
│   │
│   ├── access_mode.json              # CURRENT MODE SETTING
│   │   └─ admin | actual | alias
│   │
│   └── [source data files]
│
├── channel_summary_vectordb/         # VECTOR DATABASE
│   └─ descriptions
│   └─ dependencies
│   └─ coordinates
│   └─ oandm_manuals
│
└── lancedb_cli.py                    # SEARCH INTERFACE
```

## Access Modes

### Admin Mode
- **Input**: Accept both actual and alias names
- **Output**: Use the name the user provided
  - User says alias → respond with alias (may note resolution to actual)
  - User says actual → respond with actual only (don't mention alias)
- **Use case**: System administrators, developers

### Actual Mode
- **Input**: Only accept actual platform names
- **Output**: Show only actual names
- **Invalid input**: "This facility is not available"
- **Use case**: Internal documentation, training

### Alias Mode
- **Input**: Only accept alias platform names
- **Output**: Show ONLY alias names, NEVER reveal actual names
- **Invalid input**: "This facility is not available"
- **Use case**: External presentations, demos, public documentation
- **Generic questions**: Do not reference any platform names

## Mode Switching

```bash
# Set mode via data file
# Edit data/access_mode.json: {"mode": "admin|actual|alias"}

# Or via command (future)
# /set-mode admin
# /set-mode actual
# /set-mode alias
```

## Decision Flow by Mode

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLATFORM NAME INPUT                          │
│                    "Constitution" or "Bear"                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Load MODE from │
                    │  access_mode.json│
                    └─────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
    ┌───────────┐       ┌───────────┐       ┌───────────┐
    │   ADMIN   │       │   ACTUAL  │       │   ALIAS   │
    └───────────┘       └───────────┘       └───────────┘
          │                   │                   │
          ▼                   ▼                   ▼
    ┌───────────┐       ┌───────────┐       ┌───────────┐
    │ Is input  │       │ Is input  │       │ Is input  │
    │ actual OR │       │ actual    │       │ alias     │
    │ alias?    │       │ name?     │       │ name?     │
    └───────────┘       └───────────┘       └───────────┘
          │                   │                   │
     YES  │              YES  │  NO         YES  │  NO
          │                   │   │              │   │
          ▼                   ▼   ▼              ▼   ▼
    ┌───────────┐       ┌─────┐ ┌─────┐    ┌─────┐ ┌─────┐
    │ Resolve   │       │PROC │ │DENY │    │PROC │ │DENY │
    │ to actual │       │     │ │"not │    │     │ │"not │
    │ + proceed │       │     │ │avail│    │     │ │avail│
    └───────────┘       └─────┘ └─────┘    └─────┘ └─────┘
          │                   │                   │
          ▼                   ▼                   ▼
    ┌───────────┐       ┌───────────┐       ┌───────────┐
    │ OUTPUT:   │       │ OUTPUT:   │       │ OUTPUT:   │
    │ Use name  │       │ Show      │       │ Show      │
    │ user      │       │ actual    │       │ ONLY      │
    │ provided  │       │ names     │       │ alias     │
    └───────────┘       └───────────┘       └───────────┘
```

## Mode Examples

| Mode | User Input | System Response |
|------|------------|-----------------|
| **admin** | "Northings on Atlantis" | Shows data using "Atlantis" (no alias mentioned) |
| **admin** | "Northings on Unicorn" | Shows data using "Unicorn" (may note: resolves to Atlantis) |
| **actual** | "Northings on Atlantis" | Shows Atlantis data |
| **actual** | "Northings on Unicorn" | "This facility is not available." |
| **alias** | "Northings on Unicorn" | Shows data using "Unicorn" (NEVER reveals "Atlantis") |
| **alias** | "Northings on Atlantis" | "This facility is not available." |
