# agents/technique_selector.py

import json
import re
from typing import List, Dict
from strands import Agent
from config import Config
from utils.prompts import PromptTemplates
from .base import BaseAgent


class TechniqueSelectorAgent(BaseAgent):
    """Agent responsible for selecting appropriate therapeutic techniques with confidence scores."""
    
    def __init__(self):
        self.config = Config()
        super().__init__(
            system_prompt="You are a CBT therapist selecting appropriate techniques.",
            tools=[]
        )
    
    def select_techniques(self, history: str) -> List[Dict[str, float]]:
        """
        Dynamically select appropriate therapeutic techniques for current turn with confidence scores.
        Returns:
            List of dicts, e.g. [{"technique": "Reflection", "score": 0.9}, ...]
        """
        techniques_str = "\n".join(f"- {t}" for t in self.config.THERAPY_AGENTS)
        
        prompt = PromptTemplates.technique_selection_prompt(
            history,
            techniques_str
        )

        structured_instruction = """
        Generate the top 3 most appropriate techniques from the list above.
        Return ONLY in this JSON format:
        [
            {"technique": "<technique_name>", "score": <confidence between 0 and 1>}
        ]
        Example:
        [
            {"technique": "Reflection", "score": 0.92},
            {"technique": "Questioning", "score": 0.78}
        ]
        """

        agent = Agent(system_prompt=prompt, tools=[], model=self.model)
        response = str(agent(structured_instruction)).strip()
        print(f"[DEBUG] Raw technique selection output:\n{response}")

        # Try to extract JSON safely
        try:
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
            else:
                parsed = []
        except Exception:
            parsed = []

        # fallback manual parse if JSON failed
        if not parsed:
            parsed = []
            lines = response.split("\n")
            for line in lines:
                for t in self.config.THERAPY_AGENTS:
                    if t.lower() in line.lower():
                        score_match = re.search(r"([0-1]\.\d+)", line)
                        score = float(score_match.group(1)) if score_match else 0.5
                        parsed.append({"technique": t, "score": score})

        # filter valid techniques
        valid = [
            item for item in parsed
            if item["technique"] in self.config.THERAPY_AGENTS
        ]

        if not valid:
            print("[ERROR] No valid techniques parsed from model output.")
            print(f"[DEBUG] Raw response: {response}")
            raise ValueError("Model did not return any valid techniques or scores.")

        print(f"[DEBUG] Parsed techniques with scores: {valid}")
        return valid

    def execute(self, history: str) -> Dict[str, float]:
        """
        Execute the technique selection and return only the best one.
        Returns:
            Dict {"technique": str, "score": float}
        """
        techniques = self.select_techniques(history)
        best = max(techniques, key=lambda x: x["score"])
        print(f"[DEBUG] Selected technique: {best['technique']} (score={best['score']})")
        return best
