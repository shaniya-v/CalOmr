"""Backend package for CalOmr.

This package contains the core AI pipeline, database manager, Groq solver,
and API application.
"""

from .config import Config
from .database import DatabaseManager
from .main import CalOmrPipeline
from .groq_solver import GroqSolver
from .enhanced_pipeline import EnhancedCalOmrPipeline

__all__ = [
    'Config',
    'DatabaseManager',
    'CalOmrPipeline',
    'GroqSolver',
    'EnhancedCalOmrPipeline'
]
