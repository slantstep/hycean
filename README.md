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
