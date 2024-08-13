BVAL_1000_DESCRIPTION = """
Prior to the estimation of the diffusion tensor [@dti_1994], the diffusion data was "cropped"
to include only B values up to {max_bval} s/mm^2, following the guidelines outlined
in the paper 'A hitchhiker's guide to diffusion tensor imaging' by Mori and Zhang [@hitchhiker_dti_2006].
"""

TENSOR_ESTIMATION_DESCRIPTION = """Tensor estimation was perfomed using both the implementation in
*dipy* - `ReconstDtiFlow` [@dipy] and *MRtrix* - `dwi2tensor` & `tensor2metric` [@mrtrix3].
The diffusion tensor was fitted to the log-signal in two steps. firstly, using weighted least-squares
(WLS) with weights based on the empirical signal intensities;
secondly, by further iterated weighted least-squares (IWLS)11 with weights determined by the signal
predictions from the previous 2 iterations.

Following the estimation of the diffusion tensor, the following tensor-derived metrics were calculated:
Fractional Anisotropy (FA), Mean Diffusivity (MD), Axial Diffusivity (AD), and Radial Diffusivity (RD).
For *MRtrix*, the three Westin shape metrics were also calculated: Linearity (CL), Planarity (CP), and Sphericity (CS).
The resulting tensor-derived metrics were co-registed to the subject's T1w space using *FSL*'s `flirt` [@fsl_flirt] and
normalized to the MNI152NLin2009cAsym space using *ANTs*'s `antsApplyTransforms` [@ants].
"""
