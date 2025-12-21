# ai-ml

## OMAE 2026 - Generative AI for Marine Monitoring Documentation

Conference paper project for OMAE 2026 (Offshore Mechanics and Arctic Engineering Conference).

## Focus
Using generative AI (including agentic AI and MCPs) to improve documentation for integrated marine monitoring systems.

## Structure
```
├── ChanDefResources/       # Channel definitions and O&M manuals
│   ├── ChannelDefinitions/ # Platform channel definition files
│   ├── ChannelDefinitions-Dependency/  # Channel dependency mappings
│   ├── ChannelDependency/  # Dependency JSON files
│   ├── CoordinateSystems/  # Platform coordinate systems
│   └── OandM/              # Operations & Maintenance manuals
├── genie_mcp.py            # Databricks Genie MCP integration
├── git_instruction.md      # Git workflow guidelines
└── .mcp.json               # MCP server configuration
```

## Key Challenges Addressed
- Scattered information across documents, drawings, code, and data sources
- Inconsistent documentation varying by project and team
- Style variations based on engineering backgrounds
- Context-dependent channel definitions in source code
- Multi-format source integration (CSV, PDF, Databricks catalogs)
