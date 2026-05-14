# RWE Life Sciences MCP Server

A local **Model Context Protocol (MCP)** server that exposes a single
Real-World Evidence (RWE) tool to Claude. The tool returns aggregated,
de-identified patient cohort statistics across four dimensions:

| Dimension | Values |
|---|---|
| Age group | 0-17, 18-34, 35-49, 50-64, 65-74, 75+ |
| Gender | Male, Female, Unknown/Other |
| US Geography | 4 Census regions + all 50 states + DC |
| Longitudinal | 2018 – 2024 (year-over-year trend) |

> **Disclaimer** – All data is synthetically generated for demonstration
> purposes only. Do **not** use for clinical or regulatory decisions.

---

## Quick start

### 1. Install dependencies

```bash
cd rwe_mcp_server
pip install -r requirements.txt
```

### 2. Run the server

```bash
python server.py
```

The server starts on **stdio** (the MCP standard transport) and is ready
for Claude Desktop to connect.

---

## Connect to Claude Desktop

Open (or create) `claude_desktop_config.json`:

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

Add the server entry below (replace `/absolute/path/to/` with your actual path):

```json
{
  "mcpServers": {
    "rwe-life-sciences": {
      "command": "python",
      "args": ["/absolute/path/to/rwe_mcp_server/server.py"],
      "env": {}
    }
  }
}
```

If you use a virtual-environment interpreter:

```json
{
  "mcpServers": {
    "rwe-life-sciences": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/rwe_mcp_server/server.py"],
      "env": {}
    }
  }
}
```

Restart Claude Desktop. The 🔧 tool icon should show `rwe-life-sciences` connected.

---

## Tool reference

### `query_rwe_patient_cohort`

#### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `condition` | string | ✅ | Clinical condition (see list below) |
| `dimensions` | string[] | ❌ | Subset of `["age","gender","geography","longitudinal"]`. Default: all four. |
| `year_start` | int | ❌ | Start of observation window (2018–2024). Default `2018`. |
| `year_end` | int | ❌ | End of observation window (2018–2024). Default `2024`. |
| `region` | string | ❌ | US Census region filter: `Northeast`, `South`, `Midwest`, `West`. |

#### Supported conditions

- Type 2 Diabetes
- Hypertension
- Heart Failure
- COPD
- Asthma
- Atrial Fibrillation
- Major Depressive Disorder
- Rheumatoid Arthritis
- Chronic Kidney Disease
- Obesity

#### Example prompts for Claude

```
Show me the real-world evidence for Type 2 Diabetes across all dimensions.

What is the geographic distribution of Heart Failure patients in the Northeast between 2020 and 2024?

Compare the longitudinal trend for COPD from 2018 to 2024.

Break down Hypertension prevalence by age and gender only.
```

#### Response structure

```json
{
  "metadata": { ... },        // source, condition, ICD-10 codes, caveats
  "summary": { ... },         // total cohort KPIs
  "by_age": [ ... ],          // one row per age group
  "by_gender": [ ... ],       // one row per gender
  "by_geography": [ ... ],    // regions → states
  "longitudinal": [ ... ]     // one row per year
}
```

---

## Project layout

```
rwe_mcp_server/
├── server.py           # MCP server + tool implementation
├── requirements.txt    # Python dependencies (mcp)
└── README.md           # This file
```
