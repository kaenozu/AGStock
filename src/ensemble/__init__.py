# Ensemble module
try:
    from src.ensemble import EnsembleVoter
except ImportError:
    EnsembleVoter = None

__all__ = ["EnsembleVoter"]
