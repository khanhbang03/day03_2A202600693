# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyen Khanh Bang
- **Student ID**: 2A202600693
- **Date**: 01/06/2026

---

## I. Technical Contribution (15 Points)

I contributed to the ReAct agent implementation and supporting telemetry logic in the lab codebase.

- **Modules Implemented**:
  - `src/agent/agent.py`
  - `src/telemetry/metrics.py`
- **Code Highlights**:
  - Extended `ReActAgent.get_system_prompt()` with an explicit tool-aware instruction template.
  - Built the main `ReActAgent.run()` loop to call the LLM, parse `Action(...)` instructions, execute tools, append `Observation`, and stop on `Final Answer`.
  - Added helper methods for parsing actions and final answers.
  - Enhanced `PerformanceTracker._calculate_cost()` with a model-specific token pricing proxy.
- **Documentation**:
  - The ReAct loop now constructs a prompt that includes prior assistant responses and observations.
  - Tool calls are resolved by `_execute_tool()`, which supports callable tool definitions and returns structured observation text.
  - Telemetry logs key events: `AGENT_START`, `LLM_RESPONSE`, and `AGENT_END` for analysis.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: The agent sometimes generated an `Action` block with missing or malformed tool arguments, causing the loop to repeat without reaching a `Final Answer`.
- **Log Source**: `logs/2026-06-01.log` captured repeated `LLM_RESPONSE` events and no `AGENT_END` with a final answer.
- **Diagnosis**: The failure was caused by ambiguous prompt formatting and insufficient tool parsing rules. The model responded with partial action syntax that the parser did not handle, so the agent could not correctly execute the tool.
- **Solution**: I improved the system prompt to enforce exact `Thought`, `Action`, `Observation`, and `Final Answer` formatting. I also implemented stricter parsing logic in `agent.py` to extract tool names and argument strings, then fallback gracefully when tool execution failed.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1.  **Reasoning**: The `Thought` block forces the agent to explicitly state its reasoning before taking an action, which makes multi-step problem solving more transparent than a direct Chatbot answer.
2.  **Reliability**: The agent can perform worse than a Chatbot when the prompt is too verbose or the model produces incorrect tool calls. In those cases, a simple Chatbot answer can be more stable for short, direct queries.
3.  **Observation**: Environment feedback is essential for the next step. When the agent receives `Observation` results from a tool call, it can revise its plan or stop early with a correct final answer instead of guessing.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Use an asynchronous queue to dispatch tool calls and support a larger tool library without blocking the main reasoning loop.
- **Safety**: Implement a supervisor layer or validator that checks proposed actions before execution and rejects dangerous or unsupported tool calls.
- **Performance**: Add a retrieval layer or vector database for tool selection and allow cached observations so repeated tool queries avoid redundant work.

---

> [!NOTE]
> I confirm this report is complete and placed in the correct folder as `REPORT_[Nguyen Khanh Bang].md`.
