"""
Utility functions for the connectome module.
"""

SCALES = ["length", "invlength", "invnodevol", None]
STATS = ["sum", "mean", "min", "max"]
IN_TRACTS = ["tracts_sifted", "tracts_unsifted"]
COMBINATIONS = [
    {"in_tracts": in_tracts, "scale": scale, "stat_edge": metric}
    for in_tracts in IN_TRACTS
    for scale in SCALES
    for metric in STATS
]
