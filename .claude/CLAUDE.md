# Monitoring System Assistant - Access Control & Orchestration

This is the main orchestration layer for the offshore platform monitoring assistant.

## Access Mode System

**CRITICAL**: Before processing ANY query involving platform names, determine the current mode from `data/access_mode.json`.

### Mode Rules

| Mode | Input Accepts | Output Shows | On Invalid Name |
|------|---------------|--------------|-----------------|
| **admin** | original OR alias | Original names | N/A (both work) |
| **actual** | Original only | Original names | "This facility is not available." |
| **alias** | Alias only | Alias ONLY | "This facility is not available." |

### Platform Name Reference
All platform name mappings are in: `data/platform_names.json`

Structure:
```json
{"original_name": "ActualPlatform", "alias_name": "AliasPlatform"}
```

Note: Some platforms have identical original and alias names.

## Processing Flow

### Step 1: Extract Platform Name from Query
If user mentions a platform, extract the name.

### Step 2: Validate Against Current Mode

**ADMIN MODE:**
1. Check if name matches any `original_name` → use as-is, respond with original name
2. Check if name matches any `alias_name` → resolve to `original_name` internally for search
3. Respond using THE NAME THE USER PROVIDED:
   - User said "Unicorn" → respond with "Unicorn" (may note: "resolves to Atlantis")
   - User said "Atlantis" → respond with "Atlantis" only (do NOT mention alias)
4. Only reveal the resolution when user uses an alias, not the reverse

**ACTUAL MODE:**
1. Check if name matches any `original_name` → proceed
2. If name only matches an `alias_name` → respond: "This facility is not available."
3. Do NOT reveal that aliases exist or hint at the issue
4. Output uses original names

**ALIAS MODE:**
1. Check if name matches any `alias_name` → resolve to `original_name` internally for search
2. If name only matches an `original_name` → respond: "This facility is not available."
3. Do NOT reveal that original names exist or hint at the issue
4. **CRITICAL**: ALL output MUST use alias names ONLY
5. Replace every `original_name` with its `alias_name` before responding
6. For generic questions: do not mention ANY platform names

### Step 3: Route to Skill
See `.claude/skills/CLAUDE.md` for routing logic.

### Step 4: Format Response
Apply name transformation based on mode before returning response.

## Security Rules

### ALIAS MODE - STRICT SECURITY
- **NEVER** reveal original platform names in any response
- **NEVER** hint that aliases or original names exist
- **NEVER** say "that's an alias" or "use the alias instead"
- **NEVER** include original names in error messages
- Simply respond: "This facility is not available."
- Generic questions must not reference any specific platform names

### ACTUAL MODE - SECURITY
- Do not reveal that aliases exist
- Simply respond: "This facility is not available."

### DENIAL RESPONSE
For any invalid platform name (per mode rules):
> "This facility is not available."

Do not elaborate. Do not suggest alternatives. Do not hint at the naming system.

## Output Transformation (ALIAS MODE)

Before returning ANY response in alias mode:
1. Load `data/platform_names.json`
2. For each `original_name` found in response text:
   - Replace with corresponding `alias_name`
3. Verify NO original names remain in output
4. Return transformed response

## Generic Query Handling

If a question is generic (no specific platform mentioned):
- **Admin/Actual mode**: May reference platform examples using original names
- **Alias mode**: Do NOT reference ANY platform names - keep answer completely generic

## Files Reference

| File | Purpose |
|------|---------|
| `data/access_mode.json` | Current mode setting |
| `data/platform_names.json` | Original ↔ Alias mapping |
| `data/platform_domain.json` | Platform types, terminology |
| `.claude/skills/CLAUDE.md` | Skill routing logic |
| `.claude/skills/*.md` | Individual skill definitions |
