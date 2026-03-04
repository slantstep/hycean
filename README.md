# Hycean World Analysis Pipeline

Automated framework for identifying and characterizing Hycean exoplanet candidates using JWST transmission spectroscopy.

## Project Structure
- `hycean/` - Core pipeline modules
- `data/` - Downloaded and processed data
- `tests/` - Test suite
- `docs/` - Documentation
- `configs/` - Configuration files for planets and instruments

## Installation
```bash
conda env create -f hycean_environment.yml
conda activate hycean
```

## Quick Start
See `docs/tutorials/` for examples.

## Current Status
- [x] Phase 1: LHS 1140 b prototype (spectroscopy module)
- [ ] Phase 2: Multi-planet validation
- [ ] Phase 3: Population study
- [ ] Phase 4: Web interface

## Installation

### Prerequisites
- Python 3.11+
- conda (Miniconda or Anaconda)

### Quick Install
```bash
# Clone repository
git clone https://github.com/slantstep/hycean.git
cd hycean

# Create conda environment
conda env create -f environment_template.yml
conda activate hycean

# Verify installation
python tests/test_screening_only.py
```

### Data Requirements

The pipeline requires transmission spectra in 3-column format:
```
wavelength(µm)  depth(ppm)  error(ppm)
```

Supported formats:
- JWST/NIRISS (Cadieux et al. 2024 format)
- JWST/NIRSpec (Damiano et al. 2024 format)  
- Simple 3-column ASCII

Place spectrum files in `data/spectra/` and update planet config files accordingly.


## Data Access

### JWST Spectra
- **MAST Archive:** https://mast.stsci.edu/
- **Published papers:** Check supplementary materials
- **Contact authors:** For unpublished reduced data

### HST Spectra
- **MAST Archive:** https://archive.stsci.edu/hst/
- **Published papers:** Often include data tables
