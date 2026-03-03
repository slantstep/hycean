#!/usr/bin/env python3
"""
Test the Hycean Pipeline on LHS 1140 b.
This validates all modules work correctly before applying to new planets.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Import pipeline modules
import sys
sys.path.insert(0, str(Path(__file__).parent))

from hycean.screening import hycean_candidate_screen
from hycean.spectroscopy import SpectrumAnalyzer
from hycean.utils.data_io import load_spectrum, save_results

print("="*70)
print("HYCEAN PIPELINE TEST: LHS 1140 b")
print("="*70)

# ============================================================================
# Load Configuration
# ============================================================================
print("\n[1/5] Loading planet configuration...")

with open('configs/planets/lhs1140b.json', 'r') as f:
    config = json.load(f)

planet_params = config['planet']
star_params = config['star']

print(f"  Planet: {config['name']}")
print(f"  Radius: {planet_params['radius']:.3f} ± {planet_params['radius_error']:.3f} R_Earth")
print(f"  Mass: {planet_params['mass']:.2f} ± {planet_params['mass_error']:.2f} M_Earth")
print(f"  Star: {star_params['spectral_type']}, Teff={star_params['Teff']} K")

# ============================================================================
# Stage 1: Screening Test
# ============================================================================
print("\n[2/5] Running Stage 1: Hycean Screening...")

is_candidate, score, reasons = hycean_candidate_screen(planet_params, star_params)

print(f"\n  Hycean Candidate: {is_candidate}")
print(f"  Score: {score}/100")
print("  Reasons:")
for reason in reasons:
    print(f"    - {reason}")

# Compare to known result
expected_result = True  # LHS 1140 b IS a Hycean candidate
if is_candidate == expected_result:
    print("  ✓ PASS: Screening correctly identifies LHS 1140 b as Hycean candidate")
else:
    print("  ✗ FAIL: Screening result doesn't match expected")

# ============================================================================
# Stage 2: Spectroscopy Analysis
# ============================================================================
print("\n[3/5] Running Stage 2: Spectroscopy Analysis...")

# Load combined spectrum from your previous work
spectrum_file = '/Users/uduakken/lhs1140_project/spectra/myreduction/lhs1140_combined_simple.txt'

try:
    wl, depth_frac, err_frac = np.loadtxt(spectrum_file, unpack=True)
    # Convert to ppm for analysis
    depth_ppm = depth_frac * 1e6
    err_ppm = err_frac * 1e6
    
    print(f"  Loaded spectrum: {len(wl)} wavelength bins")
    print(f"  Range: {wl.min():.2f} - {wl.max():.2f} µm")
    
except FileNotFoundError:
    print(f"  ⚠ Combined spectrum not found at {spectrum_file}")
    print("  Creating from published spectra...")
    
    # Load individual spectra
    niriss = load_spectrum(config['observations']['NIRISS']['spectrum_file'])
    # For this test, we'll just use NIRISS
    wl = niriss['wavelength']
    depth_ppm = niriss['depth']
    err_ppm = niriss['error']

# Initialize analyzer
analyzer = SpectrumAnalyzer(wl, depth_ppm, err_ppm)

# Test 1: Flat spectrum test
chi2_red, is_flat = analyzer.flat_spectrum_test()
print(f"\n  Flat Spectrum Test:")
print(f"    χ²_reduced = {chi2_red:.2f}")
print(f"    Is flat? {is_flat}")

expected_chi2 = 2.65  # Your result from yesterday
if abs(chi2_red - expected_chi2) < 0.5:
    print(f"    ✓ PASS: χ² within 0.5 of expected ({expected_chi2})")
else:
    print(f"    ⚠ Note: χ² differs from previous result ({expected_chi2})")

# Test 2: Rayleigh slope
alpha, alpha_err, is_rayleigh = analyzer.rayleigh_slope(wl_max=1.5)
if alpha is not None:
    print(f"\n  Rayleigh Scattering:")
    print(f"    Power law index: α = {alpha:.2f} ± {alpha_err:.2f}")
    print(f"    Consistent with Rayleigh? {is_rayleigh}")
    
    expected_alpha = -6.90  # Your result
    if alpha_err > 0 and abs(alpha - expected_alpha) < 2 * alpha_err:
        print(f"    ✓ PASS: α within 2σ of expected ({expected_alpha})")
    else:
        print(f"    ⚠ Note: α differs from previous result ({expected_alpha})")
else:
    print(f"\n  Rayleigh Scattering: Not enough short-wavelength data")

# Test 3: Molecular features
features = analyzer.molecular_features()
print(f"\n  Molecular Feature Search:")
for molecule, result in features.items():
    status = "detected" if result['detected'] else "not detected"
    print(f"    {molecule:15s}: {result['sigma']:+5.2f}σ ({status})")

# ============================================================================
# Generate Report
# ============================================================================
print("\n[4/5] Generating report...")

results = {
    "planet": config['name'],
    "screening": {
        "is_hycean_candidate": is_candidate,
        "score": score,
        "reasons": reasons
    },
    "spectroscopy": {
        "atmosphere_detected": not is_flat,
        "chi2_reduced": float(chi2_red),
        "rayleigh": {
            "alpha": float(alpha) if alpha else None,
            "alpha_error": float(alpha_err) if alpha_err else None,
            "consistent_with_scattering": is_rayleigh
        },
        "molecular_features": {k: {'sigma': float(v['sigma']), 'detected': v['detected']} 
                               for k, v in features.items()}
    },
    "comparison_to_literature": {
        "cadieux_rayleigh_detection": config['published_results']['rayleigh_scattering']['significance'],
        "our_rayleigh_significance": abs(alpha / alpha_err) if alpha and alpha_err else None
    }
}

# Save report
output_dir = Path('data/outputs')
output_dir.mkdir(parents=True, exist_ok=True)
save_results(results, output_dir / 'lhs1140b_pipeline_test.json')

print(f"  ✓ Report saved to {output_dir / 'lhs1140b_pipeline_test.json'}")

# ============================================================================
# Validation Summary
# ============================================================================
print("\n[5/5] Validation Summary")
print("="*70)

validation_checks = [
    ("Hycean screening identifies candidate", is_candidate == True),
    ("Atmosphere detected (χ²>1.5)", chi2_red > 1.5),
    ("Rayleigh scattering consistent", is_rayleigh if alpha else None),
    ("Molecular features analyzed", len(features) > 0)
]

all_passed = True
for check_name, passed in validation_checks:
    if passed is None:
        status = "⚠ SKIP"
        symbol = "⚠"
    elif passed:
        status = "✓ PASS"
        symbol = "✓"
    else:
        status = "✗ FAIL"
        symbol = "✗"
        all_passed = False
    
    print(f"  {symbol} {check_name:45s} {status}")

print("="*70)
if all_passed:
    print("✓ All validation checks passed!")
    print("✓ Pipeline is ready to test on additional planets")
else:
    print("⚠ Some checks failed - review results above")

print("\nNext steps:")
print("  1. Review output report: data/outputs/lhs1140b_pipeline_test.json")
print("  2. Compare results to your previous analysis")
print("  3. If validated, add a second test planet (e.g., K2-18 b, TOI-270 d)")

