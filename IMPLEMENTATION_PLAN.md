# Monitoring System Assistant - Implementation Plan

## Overview

Recreate the OpenAI Agent Builder flow using Claude Code capabilities:
- **MCP Server** for LanceDB vector search
- **Claude Skills** for specialized agent behaviors
- **Orchestration** via main assistant prompt

## Architecture Comparison

| OpenAI Agent Builder | Claude Implementation |
|---------------------|----------------------|
| Vector Store Tools | MCP Server (LanceDB) |
| Agent Nodes | Claude Skills (`.md` files) |
| Workflow Routing | System prompt + tool selection |
| Guardrails | Skill with validation logic |
| Output Schema | Structured tool responses |

## Component Design

### 1. MCP Server: `lancedb_mcp.py`

A FastMCP server exposing LanceDB search as tools:

```python
@mcp.tool()
async def search_descriptions(query: str, platform: str = None, limit: int = 5) -> str:
    """Search channel descriptions by semantic similarity"""

@mcp.tool()
async def search_dependencies(query: str, platform: str = None, limit: int = 5) -> str:
    """Search channel dependencies and lineage"""

@mcp.tool()
async def search_coordinates(query: str, platform: str = None, limit: int = 5) -> str:
    """Search platform/sensor coordinate systems"""

@mcp.tool()
async def search_oandm(query: str, platform: str = None, limit: int = 5) -> str:
    """Search O&M manual content"""

@mcp.tool()
async def get_channel_lineage(channel_name: str, platform: str) -> str:
    """Get upstream/downstream channels for a specific channel"""
```

### 2. Skills Structure

```
.claude/commands/
├── monitoring-assistant.md      # Main orchestrator
├── select-type.md               # Question classifier
├── channel-resolver.md          # Resolve ambiguous channel references
├── channel-description.md       # Describe channels
├── channel-dependency.md        # Explain lineage/processing
├── coordinate-system.md         # Platform coordinate info
└── other-na.md                  # General naval architecture
```

### 3. Skill Definitions

#### 3.1 Main Orchestrator: `monitoring-assistant.md`
```markdown
# Monitoring System Assistant

You are a monitoring system assistant for offshore platforms (IMMS/EPRMS).

## Workflow
1. Classify the question type using select-type logic
2. If channel-related, resolve the specific channel first
3. Route to appropriate specialist logic
4. Synthesize final answer

## Tools Available
- search_descriptions: Find channel definitions
- search_dependencies: Find channel lineage
- search_coordinates: Find platform/sensor coordinates
- search_oandm: Search O&M manuals

## Question Types
- channel-description: What is X channel?
- channel-dependency: How is X derived? What feeds X?
- coordinate-system: What is the coordinate system for platform Y?
- other: General naval architecture questions
```

#### 3.2 Select Type: `select-type.md`
```markdown
Classify the user question and extract context.

## Classification Rules

Set question_type = "coordinate-system" when:
- Question about coordinate systems, reference frames, axes, heading
- Direction/orientation channels (wind dir, current dir, heading)
- Motion quantities (surge, sway, heave, roll, pitch, yaw)

Set question_type = "channel-dependency" when:
- User asks if channel is raw vs derived
- How a signal is computed/processed
- Mentions: best, derived, processed, PQ, True, corrected
- Lineage or source channel questions

Set question_type = "channel-description" when:
- Simple "what is X" questions about channels
- Units, meaning, purpose of a channel

Set question_type = "other" when:
- General naval architecture concepts
- Not specific to channels or coordinates

## Output
{
  "question_type": "channel-description|channel-dependency|coordinate-system|other",
  "platform": "<extracted platform name or empty>",
  "system": "<extracted system name or empty>",
  "device": "<extracted device name or empty>",
  "needs_coordinate_info": boolean,
  "needs_dependency_info": boolean
}
```

#### 3.3 Channel Resolver: `channel-resolver.md`
```markdown
Resolve ambiguous channel references to a specific channel.

## Process
1. Search dependencies table for matching channels
2. Identify all candidates for the quantity mentioned
3. Follow edges to find terminal/derived channel
4. If user specified exact name, use that; otherwise prefer "Best" variant

## Resolution Rules
- Terminal channel = has inputs but no outputs for same quantity
- "Best", "Derived", "PQ" labels indicate final processed value
- Raw channels have no upstream inputs

## Output
{
  "resolved_channel_id": string,
  "resolved_channel_name": string,
  "resolved_device": string,
  "resolved_is_derived": boolean,
  "resolved_raw_sources": string,
  "resolver_notes": string
}
```

## 4. Implementation Phases

### Phase 1: MCP Server (Day 1)
- [ ] Create `lancedb_mcp.py` with search tools
- [ ] Add to `.mcp.json` configuration
- [ ] Test each tool independently
- [ ] Verify embedding model loads correctly

### Phase 2: Core Skills (Day 2)
- [ ] Create `monitoring-assistant.md` main skill
- [ ] Create `select-type.md` classifier
- [ ] Create `channel-resolver.md`
- [ ] Test routing logic

### Phase 3: Specialist Skills (Day 3)
- [ ] Create `channel-description.md`
- [ ] Create `channel-dependency.md`
- [ ] Create `coordinate-system.md`
- [ ] Create `other-na.md`

### Phase 4: Integration & Testing (Day 4)
- [ ] End-to-end testing with sample questions
- [ ] Refine prompts based on results
- [ ] Add guardrails/validation
- [ ] Document usage

## 5. Sample Questions for Testing

| Question | Expected Route | Expected Behavior |
|----------|---------------|-------------------|
| "What is roll rate on Constitution?" | description | Resolve to Roll Rate channel, return definition |
| "How is Best Wind Speed derived on Atlantis?" | dependency | Show EC/WC sources feeding Best |
| "What is the coordinate system for Holstein?" | coordinates | Return +X, +Y, +Z orientation |
| "What is surge motion?" | description | General channel description |
| "Is heave acceleration raw or derived?" | dependency | Check lineage, explain processing |

## 6. File Structure After Implementation

```
prototypes/git/
├── channel_summary_vectordb/     # LanceDB database
│   ├── descriptions.lance
│   ├── dependencies.lance
│   ├── coordinates.lance
│   └── oandm_manuals.lance
├── lancedb_mcp.py                # MCP server for LanceDB
├── .mcp.json                     # MCP configuration
└── .claude/
    └── commands/
        ├── monitoring-assistant.md
        ├── select-type.md
        ├── channel-resolver.md
        ├── channel-description.md
        ├── channel-dependency.md
        ├── coordinate-system.md
        └── other-na.md
```

## 7. Alternative Approaches

### Option A: Single Skill + MCP Tools (Simpler)
- One comprehensive skill with routing logic
- MCP provides all search tools
- Claude handles orchestration naturally
- **Pros**: Simpler, leverages Claude's reasoning
- **Cons**: Less modular, harder to debug individual components

### Option B: Multi-Skill Pipeline (Current Plan)
- Separate skills for each agent role
- Explicit routing between skills
- **Pros**: Mirrors OpenAI flow, modular
- **Cons**: More complex, may over-engineer

### Option C: Python Agent with Claude API
- Python script using Claude API
- Explicit workflow control in code
- **Pros**: Full control, can add custom logic
- **Cons**: More development effort, not using Claude Code native features

## 8. Recommended Approach

**Start with Option A** (Single Skill + MCP):
1. Build MCP server first - this is reusable regardless of approach
2. Create one main skill that uses the MCP tools
3. Let Claude handle routing internally
4. If needed, split into multiple skills later

This gives faster time-to-value and leverages Claude's natural ability to:
- Classify questions
- Chain tool calls
- Synthesize responses

## 9. Benefits of This Approach

### 9.1 Comparison: OpenAI Agent Builder vs Claude Skills + MCP

| Aspect | OpenAI Agent Builder | Claude Skills + MCP |
|--------|---------------------|---------------------|
| **Setup** | GUI-based, cloud-hosted | File-based, local or cloud |
| **Version Control** | Limited | Full git integration |
| **Customization** | Drag-drop nodes | Markdown + Python |
| **Data Privacy** | Data sent to OpenAI | Local vector DB (LanceDB) |
| **Cost** | Per-token + platform fees | Per-token only |
| **Debugging** | Black-box workflow | Transparent tool calls |
| **Portability** | Locked to platform | Portable files |

### 9.2 Benefits of Modular Skills Architecture

#### **Separation of Concerns**
```
┌─────────────────────┐
│ monitoring-assistant│ → Orchestration & routing logic
├─────────────────────┤
│ channel-description │ → Domain: What channels measure
│ channel-dependency  │ → Domain: How channels relate
│ coordinate-system   │ → Domain: Spatial information
│ oandm-search        │ → Domain: Documentation
│ channel-resolver    │ → Utility: Disambiguation
└─────────────────────┘
```

Each skill has **one responsibility**, making it:
- Easier to test individually
- Easier to update without breaking others
- Easier to understand and maintain

#### **Reusability**
- Skills can be invoked directly: `/channel-description roll rate`
- Or composed by the orchestrator
- Can be reused in other projects

#### **Transparency**
- All prompts are visible in `.md` files
- Tool calls are logged
- No black-box workflow

#### **Iterative Improvement**
- Refine one skill without touching others
- A/B test different skill versions
- Track changes in git

### 9.3 Benefits of Local LanceDB + MCP

#### **Data Privacy**
- Vector database stays on your machine
- No proprietary data sent to external services
- O&M manuals remain confidential

#### **Performance**
- Local embedding model (all-MiniLM-L6-v2)
- Sub-second search latency
- No network roundtrips for vector search

#### **Cost Efficiency**
- No vector database hosting fees
- No embedding API costs
- Only pay for Claude API tokens

#### **Flexibility**
- Easy to add new data (just add to LanceDB)
- Easy to update embeddings
- Can switch embedding models

### 9.4 Benefits for OMAE Paper

This implementation demonstrates:

1. **Practical AI Integration**: Real working system, not just concept
2. **Multi-Source RAG**: Combines descriptions, dependencies, coordinates, O&M docs
3. **Domain-Specific AI**: Tailored for offshore monitoring systems
4. **Reproducibility**: All code and prompts available for review
5. **Scalability**: Pattern works for any number of platforms/channels

### 9.5 Comparison Table: Architecture Patterns

| Pattern | Pros | Cons | Best For |
|---------|------|------|----------|
| **Single Monolithic Prompt** | Simple | Hard to maintain | Prototypes |
| **Multi-Skill (This approach)** | Modular, testable | More files | Production |
| **Code-Based Agent** | Full control | More development | Complex logic |
| **External Platform** | GUI, no-code | Vendor lock-in | Non-technical users |

## 10. Final Architecture

```
prototypes/git/
├── channel_summary_vectordb/           # Local vector database
│   ├── descriptions.lance              # 11,755 channel definitions
│   ├── dependencies.lance              # 12,938 channel relationships
│   ├── coordinates.lance               # 354 sensor locations
│   └── oandm_manuals.lance             # 8,720 O&M text chunks
│
├── lancedb_mcp.py                      # MCP server (6 tools)
├── .mcp.json                           # MCP configuration
│
├── .claude/
│   ├── commands/
│   │   ├── monitoring-assistant.md     # Main orchestrator
│   │   ├── channel-description.md      # Specialist: definitions
│   │   ├── channel-dependency.md       # Specialist: lineage
│   │   ├── coordinate-system.md        # Specialist: coordinates
│   │   ├── oandm-search.md             # Specialist: O&M docs
│   │   └── channel-resolver.md         # Utility: disambiguation
│   └── settings.local.json             # Permissions
│
├── data/                               # Source data files
│   ├── descriptions/
│   ├── dependencies/
│   ├── coordinates/
│   └── OandM/
│
└── IMPLEMENTATION_PLAN.md              # This document
```

## 11. Usage Examples

```bash
# From prototypes/git folder:

# Main assistant (routes automatically)
/monitoring-assistant What is roll rate on Constitution?

# Direct specialist access
/channel-description heave acceleration on Atlantis
/channel-dependency How is Best Wind Speed derived on Mars?
/coordinate-system What is the coordinate system for Holstein?
/oandm-search calibration procedure for 6DOF on Boomvang
/channel-resolver Resolve wind speed on Atlantis
```

## 12. Next Steps

1. **Test the system** from `prototypes/git` folder
2. **Refine prompts** based on actual usage
3. **Add more platforms** to the vector database as needed
4. **Document for OMAE paper** - this implementation demonstrates practical AI for offshore monitoring
