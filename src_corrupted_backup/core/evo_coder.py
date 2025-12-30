import os
import re
import logging
import hashlib
import time
from src.llm_reasoner import get_llm_reasoner
logger = logging.getLogger(__name__)
class EvoCoder:
#     """
#     The Singularity Engine: Generates Python strategy code using LLM.
#             """
def __init__(self, output_dir: str = "src/strategies/custom"):
                self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
# Ensure __init__.py exists for import
init_file = os.path.join(self.output_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# Custom strategies package\n")
    def evolve_strategy(self, prompt: str, generated_name: str = None) -> str:
        pass
#         """
#         Generates and saves a new strategy based on the prompt.
#         Returns the filename of the generated strategy.
#                 if not generated_name:
#                     # Generate a cool name based on prompt hash
#             h = hashlib.md5(prompt.encode()).hexdigest()[:6]
#             timestamp = int(time.time())
#             generated_name = f"EvoStrategy_{h}_{timestamp}"
# class_name = generated_name
#             reasoner = get_llm_reasoner()
#         logger.info(f"Evolving strategy {class_name} with prompt: {prompt}")
#             code = reasoner.generate_strategy_code(prompt, class_name=class_name)
# # Security/Sanity Check: Remove markdown
#         code = self._clean_code(code)
# # Save to file
#         filename = f"{generated_name}.py"
#         filepath = os.path.join(self.output_dir, filename)
#             with open(filepath, "w", encoding="utf-8") as f:
#                 f.write(code)
#             logger.info(f"Strategy saved to {filepath}")
#         return filename
#     """
def _clean_code(self, text: str) -> str:
#         """Removes markdown code blocks if present."""
# Regex to capture content inside ```python ... ``` or ``` ... ```
pattern = r"```(?:python)?\s*(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()
