"""Main TUI implementation for squid

Author: Finlay Clark  
Created: 2024
"""


import py_cui

__version__ = "v0.0.1"

from .app import SquidApp, main
from .slurm import SlurmQueue
