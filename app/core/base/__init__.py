"""Base module for core game components.

This module contains fundamental game elements and systems that form the foundation
of the Sanguosha game engine.
"""

from .enums import *
from .fsm import *
from .game import *
from .game_engine import *
from .path_utils import *
from .state import *
from .game_elements import *
from .element_adapter import *

__all__ = [
    # Existing exports
    'enums', 'fsm', 'game', 'game_engine', 'path_utils', 'state',
    # New game elements exports
    'BaseElement', 'CardElement', 'HealthElement', 'FactionElement', 
    'EquipmentElement', 'DistanceElement', 'ElementBasedAdjudicationEngine',
    'ElementPlayerAdapter'
]