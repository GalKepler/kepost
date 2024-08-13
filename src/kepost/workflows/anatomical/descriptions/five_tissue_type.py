FIVE_TISSUE_FSL_DESCRIPTION = """
For later inclusion in the Anatomically-constrained tractography (ACT)[@act2012],
*FSL*'s BET[@fsl_bet], FAST[@fsl_fast] and FIRST[@fsl_first] were used to segment the T1w image into five tissue types, as implemented in *MRtrix*'s `5ttgen`:
cortical gray matter (GM), sub-cortical gray matter, white matter (WM), cerebrospinal fluid (CSF),
and pathological tissue.
"""

FIVE_TISSUE_HSVS_DESCRIPTION = """
For later inclusion in the Anatomically-constrained tractography (ACT)[@act2012],
A hybrid surface/volume segmentation was created [@hsvs_2020] through *FreeSurfer* and *FSL* tools,
as implemented in *MRtrix*'s `5ttgen`, to segment the T1w image into five tissue types:
cortical gray matter (GM), sub-cortical gray matter, white matter (WM), cerebrospinal fluid (CSF),
and pathological tissue.
"""
