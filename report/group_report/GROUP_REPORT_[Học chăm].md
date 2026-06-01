# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Học chăm
- **Team Members**: Nguyễn Khánh Bằng, Nguyễn Văn Quang, Mã Vĩnh Lộc, Phạm Trần Nguyên Phú
- **Deployment Date**: 2026-06-01

---

## 1. Executive Summary

Our group implemented a ReAct-style agent for Lab 3 that moves beyond a normal chatbot by allowing the model to reason, select a tool, observe the result, and continue until it can produce a final answer. The implementation focuses on the core production loop: tool-aware prompting, action parsing, tool execution, observation history, final-answer detection, provider abstraction, and structured telemetry.

- **Success Rate**: 5/5 successful cases in the deterministic smoke evaluation logged on 2026-06-01.
- **Baseline Comparison**: The chatbot baseline can answer simple direct questions, but it has no action/observation loop, so it cannot reliably solve tool-dependent multi-step tasks without guessing.
- **Key Outcome**: The ReAct agent solved representative multi-step tasks by calling tools and feeding observations back into the next prompt, while also surfacing tool failures instead of silently hallucinating.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

The final agent follows this control flow:

```text
User Input
   |
   v
System Prompt + Tool Descriptions
   |
   v
LLM Response
   |
   +--> Final Answer found? --> return answer
   |
   +--> Action found? --> parse tool_name(args)
                         |
                         v
                    Execute registered tool
                         |
                         v
                    Append Observation to history
                         |
                         v
                    Repeat until Final Answer or max_steps
```

Implementation details:

- `ReActAgent.run()` calls the configured `LLMProvider`, logs each response, parses `Action: tool_name(arguments)`, executes the matching tool, and appends `Observation` back into the prompt.
- `_extract_action()` uses a strict regex format so tool calls are predictable.
- `_extract_final_answer()` stops the loop when the model produces `Final Answer:`.
- `_execute_tool()` dispatches registered callables from `function`, `executor`, or `callable`.
- `max_steps=5` prevents endless loops and runaway billing.

### 2.2 Tool Definitions (Inventory)

The current agent supports any registered callable tool with a name and description. The deterministic evaluation used the following representative e-commerce tools:

| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `check_stock` | `string`, for example `iPhone` | Check whether a requested item is available. |
| `get_discount` | `string`, for example `WINNER` | Retrieve the discount percentage for a coupon code. |
| `calc_shipping` | `string`, for example `1kg,Hanoi` | Estimate shipping cost from weight and destination. |

Tool design evolved from vague descriptions to explicit names, purpose, and argument examples. This reduced confusion because the model only knows tools through the prompt text it receives.

### 2.3 LLM Providers Used

- **Primary**: `OpenAIProvider` with `gpt-4o` through the configured OpenAI-compatible MIMO endpoint.
- **Secondary (Backup)**: `GeminiProvider` with `gemini-1.5-flash`.
- **Local Fallback**: `LocalProvider` using a Phi-3-mini GGUF model through `llama-cpp-python`.

The shared `LLMProvider` interface lets the agent switch providers without changing the ReAct loop.

---

## 3. Telemetry & Performance Dashboard

Telemetry is captured through structured JSON events:

- `AGENT_START`
- `LLM_RESPONSE`
- `AGENT_END`
- `LLM_METRIC` from `PerformanceTracker`

Final smoke-run source: `logs/2026-06-01.log`

| Metric | Result |
| :--- | :--- |
| Test Tasks | 5 |
| LLM Calls | 9 |
| Agent Success Rate | 5/5 = 100% |
| Average Loop Count | 0.8 tool steps per task |
| Average Tokens per Task | 41.8 tokens |
| Total Tokens | 209 tokens |
| Average Latency (P50) | 0 ms in deterministic fake-provider run |
| Max Latency (P99 proxy) | 0 ms in deterministic fake-provider run |
| Total Real API Cost | $0.0000 for the fake-provider smoke run |
| Proxy Cost Estimate | About $0.0021 using the fallback `$0.01 / 1K tokens` estimator |

Important limitation: the local smoke evaluation validates the agent loop and telemetry path, but it is not a live OpenAI/Gemini latency benchmark. A production benchmark should rerun the same cases against the real provider and compare P50/P99 latency, token usage, and cost.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study 1: Malformed Action Syntax

- **Input**: `Malformed action falls back to content`
- **Trace**: The model returned `Action check_stock iPhone` instead of `Action: check_stock(iPhone)`.
- **Observation**: `_extract_action()` did not match the malformed format, so the agent returned the raw model content instead of executing a tool.
- **Root Cause**: The parser intentionally accepts only the strict `Action: tool_name(arguments)` pattern. This makes normal tool calls predictable, but weak model formatting can still bypass the tool path.
- **Fix Applied**: The system prompt documents the exact required format, and the agent now falls back gracefully instead of crashing.
- **Future Improvement**: Add a parser retry: when text looks like an action but fails validation, ask the model to reformat once before ending.

### Case Study 2: Hallucinated Tool Name

- **Input**: `Unknown tool failure is surfaced`
- **Trace**: The model attempted `Action: lookup_price(iPhone)`.
- **Observation**: The agent returned `Tool lookup_price not found.` and continued to a final answer explaining that price could not be verified.
- **Root Cause**: The model selected a plausible but unregistered tool name.
- **Fix Applied**: `_execute_tool()` now returns an explicit not-found observation, allowing the model to recover instead of pretending the tool succeeded.
- **Future Improvement**: Add a tool-name validator that rejects unknown actions before execution and reminds the model of valid tool names.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Skeleton Agent vs Implemented ReAct Agent

- **Diff**: Replaced the placeholder `run()` behavior with LLM generation, action parsing, callable tool dispatch, observation history, final-answer extraction, and final telemetry.
- **Before**: The skeleton returned `Not implemented. Fill in the TODOs!`.
- **After**: The implemented agent passed 5/5 deterministic smoke cases.
- **Result**: The ReAct loop changed the system from a static placeholder into a working multi-step agent.

### Experiment 2: Tool Failure Handling

- **Diff**: Added explicit fallback output for missing tools and tool execution exceptions.
- **Result**: A hallucinated `lookup_price` call did not crash the run. The failure became an observation that the model could use in its final answer.

### Experiment 3: Chatbot vs Agent

| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Simple definition question | Correct direct answer | Correct final answer | Draw |
| Stock lookup | Guesses or says it cannot verify | Calls `check_stock` and answers from observation | **Agent** |
| Coupon + stock multi-step task | Likely incomplete because no tools are available | Calls `check_stock`, then `get_discount`, then answers | **Agent** |
| Unknown tool/capability | May hallucinate an answer | Reports the unavailable tool clearly | **Agent** |
| Malformed model output | Not applicable | Falls back without crashing | **Agent** |

Main group insight: the final answer is less important than the trace. The trace shows whether the agent truly used evidence or simply sounded confident.

---

## 6. Production Readiness Review

- **Security**: Keep tool execution behind an allowlist, validate argument strings, and avoid exposing file/network tools without a policy layer.
- **Guardrails**: Keep `max_steps`, add parser retries, reject unknown tool names, and log structured error codes for parser failures, tool failures, and timeouts.
- **Observability**: Continue logging `AGENT_START`, `LLM_RESPONSE`, `AGENT_END`, token usage, latency, and cost estimates. Add a script to aggregate logs into a dashboard.
- **Reliability**: Move from regex-only parsing toward JSON schema or Pydantic validation for tool calls.
- **Scaling**: For more complex workflows, move from a single loop to a graph-based design such as LangGraph, with separate nodes for planning, validation, tool execution, and final response.
- **Provider Strategy**: Keep OpenAI as the primary path, Gemini as a fallback, and local Phi-3-mini for offline testing or low-cost development.

---

> [!NOTE]
> This report is complete and placed in the required folder as `GROUP_REPORT_[Học chăm].md`.
