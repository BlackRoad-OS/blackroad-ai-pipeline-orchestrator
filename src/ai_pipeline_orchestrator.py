#!/usr/bin/env python3
"""BlackRoad AI Pipeline Orchestrator — chain AI tasks with retry/fallback."""
import json, time, os, urllib.request

GATEWAY_URL = os.environ.get("BLACKROAD_GATEWAY_URL", "http://127.0.0.1:8787")

class PipelineStep:
    def __init__(self, name: str, intent: str, agent: str = "octavia"):
        self.name = name; self.intent = intent; self.agent = agent
    def __repr__(self): return f"Step({self.name})"

class Pipeline:
    def __init__(self, name: str):
        self.name = name
        self.steps: list[PipelineStep] = []
        self.results = []

    def add(self, name: str, intent: str, agent: str = "octavia") -> "Pipeline":
        self.steps.append(PipelineStep(name, intent, agent))
        return self

    def run(self, initial_input: str = "", max_retries: int = 2) -> list:
        print(f"\\n🔄 Pipeline: {self.name} ({len(self.steps)} steps)\\n")
        context = initial_input
        for step in self.steps:
            print(f"  ▶ {step.name}...")
            for attempt in range(max_retries + 1):
                try:
                    result = self._call_agent(step.agent, step.intent, context)
                    context = result.get("output", "")
                    self.results.append({"step": step.name, "output": context[:200]})
                    print(f"  ✓ {step.name} ({len(context)} chars)")
                    break
                except Exception as e:
                    if attempt == max_retries:
                        print(f"  ✗ {step.name} failed: {e}")
                        self.results.append({"step": step.name, "error": str(e)})
                    else:
                        time.sleep(2 ** attempt)
        return self.results

    def _call_agent(self, agent: str, intent: str, context: str) -> dict:
        payload = json.dumps({"agent": agent, "intent": intent, "input": context}).encode()
        req = urllib.request.Request(f"{GATEWAY_URL}/v1/agent", data=payload,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())

if __name__ == "__main__":
    pipe = (Pipeline("world-analysis")
        .add("summarize", "Summarize the key themes of the BlackRoad world ecosystem", "lucidia")
        .add("critique", "Critique and suggest improvements to the summary", "octavia"))
    results = pipe.run("BlackRoad is an AI-first platform with 30k agents and live world generation")
    print("\\nResults:", json.dumps(results, indent=2))

