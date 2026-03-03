#!/usr/bin/env python3
"""Test screening on all planets to verify pipeline differentiation."""

import json
from pathlib import Path
from hycean.screening import hycean_candidate_screen

with open('configs/planet_database.json', 'r') as f:
    database = json.load(f)

print("="*70)
print("SCREENING TEST: Hycean Differentiation")
print("="*70)

results = []

for planet_entry in database['planets']:
    config_file = planet_entry['config_file']
    
    if not Path(config_file).exists():
        continue
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    planet_params = config['planet']
    star_params = config['star']
    
    is_candidate, score, reasons = hycean_candidate_screen(planet_params, star_params)
    
    expected = planet_entry['expected_hycean']
    match = "✓" if is_candidate == expected else "✗ MISMATCH"
    
    results.append({
        'name': planet_entry['name'],
        'score': score,
        'hycean': is_candidate,
        'expected': expected,
        'match': match
    })

print(f"\n{'Planet':<20s} {'Score':<8s} {'Hycean?':<10s} {'Expected':<10s} {'Match'}")
print("-"*70)

for r in results:
    hycean_str = "Yes" if r['hycean'] else "No"
    expected_str = "Yes" if r['expected'] else "No"
    print(f"{r['name']:<20s} {r['score']:>3d}/100  {hycean_str:<10s} {expected_str:<10s} {r['match']}")

print("="*70)

# Count matches
matches = sum(1 for r in results if "✓" in r['match'])
total = len(results)
print(f"\nScreening Accuracy: {matches}/{total} ({100*matches/total:.0f}%)")
