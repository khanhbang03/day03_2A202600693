import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        TODO: Implement the system prompt that instructs the agent to follow ReAct.
        Should include:
        1.  Available tools and their descriptions.
        2.  Format instructions: Thought, Action, Observation.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
        You are an intelligent assistant. You have access to the following tools:
        {tool_descriptions}

        Use the following format:
        Thought: your line of reasoning.
        Action: tool_name(arguments)
        Observation: result of the tool call.
        ... (repeat Thought/Action/Observation if needed)
        Final Answer: your final response.
        """

    def run(self, user_input: str) -> str:
        """
        TODO: Implement the ReAct loop logic.
        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        self.history = []
        current_prompt = user_input
        steps = 0
        answer = None

        while steps < self.max_steps:
            # TODO: Generate LLM response
            result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            content = result.get("content", "").strip()
            logger.log_event("LLM_RESPONSE", {
                "prompt": current_prompt,
                "content": content,
                "usage": result.get("usage"),
                "latency_ms": result.get("latency_ms")
            })

            # TODO: Parse Thought/Action from result
            action_data = self._extract_action(content)

            # TODO: If Action found -> Call tool -> Append Observation
            if action_data:
                observation = self._execute_tool(action_data["name"], action_data["args"])
                self.history.append({"role": "assistant", "content": content})
                self.history.append({"role": "observation", "content": observation})
                current_prompt = f"{user_input}\n\n{self._format_history()}"
                steps += 1
                continue

            # TODO: If Final Answer found -> Break loop
            answer = self._extract_final_answer(content)
            if answer:
                self.history.append({"role": "assistant", "content": content})
                break

            if content:
                answer = content
                break

            steps += 1

        if answer is None:
            answer = "I could not determine a final answer from the model output."

        logger.log_event("AGENT_END", {"steps": steps, "final_answer": answer})
        return answer

    def _format_history(self) -> str:
        formatted_entries = []
        for item in self.history:
            if item["role"] == "assistant":
                formatted_entries.append(item["content"])
            elif item["role"] == "observation":
                formatted_entries.append(f"Observation: {item['content']}")
        return "\n".join(formatted_entries)

    def _extract_action(self, text: str):
        match = re.search(r"Action:\s*([A-Za-z_][A-Za-z0-9_]*)\((.*?)\)", text, re.DOTALL)
        if not match:
            return None
        return {
            "name": match.group(1).strip(),
            "args": match.group(2).strip()
        }

    def _extract_final_answer(self, text: str) -> Optional[str]:
        match = re.search(r"Final Answer:\s*(.+)$", text, re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return match.group(1).strip()

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Helper method to execute tools by name.
        """
        for tool in self.tools:
            if tool['name'] == tool_name:
                # TODO: Implement dynamic function calling or simple if/else
                function = tool.get("function") or tool.get("executor") or tool.get("callable")
                if callable(function):
                    try:
                        return function(args) if args else function()
                    except TypeError:
                        return function(args)
                    except Exception as exc:
                        return f"Tool {tool_name} failed: {exc}"
                return tool.get("description", f"Executed {tool_name} with args: {args}")
        return f"Tool {tool_name} not found."