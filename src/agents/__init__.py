"""
Expose legacy agent classes defined in the top-level `src/agents.py` module.
The package name conflicts with the module name, so we load the module under
a temporary alias to avoid circular imports during package initialization.
"""

import importlib.util
import sys
from pathlib import Path

# Load the legacy module once under a unique name
_module_name = "_src_agents_legacy"
if _module_name not in sys.modules:
    _agents_path = Path(__file__).resolve().parent.parent / "agents.py"
    spec = importlib.util.spec_from_file_location(_module_name, _agents_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    sys.modules[_module_name] = module
else:
    module = sys.modules[_module_name]

# Re-export expected symbols for tests
Agent = module.Agent
AgentVote = module.AgentVote
TechnicalAnalyst = module.TechnicalAnalyst
FundamentalAnalyst = module.FundamentalAnalyst
MacroStrategist = module.MacroStrategist
RiskManager = module.RiskManager
PortfolioManager = module.PortfolioManager

__all__ = [
    "Agent",
    "AgentVote",
    "TechnicalAnalyst",
    "FundamentalAnalyst",
    "MacroStrategist",
    "RiskManager",
    "PortfolioManager",
]
