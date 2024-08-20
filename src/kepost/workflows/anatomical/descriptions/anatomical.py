ANATOMICAL_BASE_WORKFLOW_DESCRIPTION = """
**Anatomical data post-processing**

: The following parcellation atlases were processed: {atlases}.
Each parcellation atlas was transformed to the subject's T1w-reference image using `antsApplyTransforms`
distributed with ANTs {ants_ver} [@ants, RRID:SCR_004757] and cropped to the subject's grey matter using
`fslmaths` distributed with FSL {fsl_ver} [@fsl, RRID:SCR_002823].
"""
