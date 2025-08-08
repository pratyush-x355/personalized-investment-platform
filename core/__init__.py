# core/__init__.py
"""
Core trading module containing Kite API wrapper and other trading utilities.
"""

from .kite_wrapper import Kite_Api

# Optional: You can also expose specific classes/functions for easier access
__all__ = ['Kite_Api']

# Optional: Version information
__version__ = '1.0.0'