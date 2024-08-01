"""
Utility functions for the connectome module.
"""

SCALES = ["length", "invlength", "invnodevol", None]
STATS = ["sum", "mean", "min", "max"]
COMBINATIONS = [
    {"scale": scale, "stat_edge": metric} for scale in SCALES for metric in STATS
]
