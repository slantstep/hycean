#!/usr/bin/env python3
"""
Batch process multiple planets through the pipeline.
"""

import json
from pathlib import Path
from hycean import HyceanPipeline

# Load planet database
with open('configs/planet_database.json', 'r') as f:
    database = json.load(f)

print("="*70)
print("BATCH PROCESSING: Hycean Pipeline with QHF Habitability")
print("="*70)

results_summary = []

for planet_entry in database['planets']:
    config_file = planet_entry['config_file']
    
    if not Path(config_file).exists():
        print(f"\n⚠ Config not found: {config_file} - skipping")
        continue
    
    try:
        pipeline = HyceanPipeline(config_file)
        results = pipeline.run_full_pipeline()
        
        # Add to summary
        summary = {
            'planet': planet_entry['name'],
            'hycean_candidate': results.get('screening', {}).get('is_hycean_candidate', False),
            'hycean_score': results.get('screening', {}).get('score', 0),
            'atmosphere_detected': results.get('spectroscopy', {}).get('atmosphere_detected', None),
            'qhf_eta': results.get('habitability', {}).get('eta', None),
            'qhf_habitable': results.get('habitability', {}).get('potentially_habitable', None)
        }
        results_summary.append(summary)
        
    except Exception as e:
        print(f"\n✗ Error processing {planet_entry['name']}: {e}")
        import traceback
        traceback.print_exc()
        continue

# Print summary table
print("\n" + "="*70)
print("BATCH PROCESSING SUMMARY")
print("="*70)
print(f"{'Planet':<20s} {'Hycean?':<10s} {'Score':<8s} {'Atm?':<8s} {'η':<8s} {'Habitable?'}")
print("-"*70)

for summary in results_summary:
    planet = summary['planet']
    hycean = "✓ Yes" if summary['hycean_candidate'] else "✗ No"
    score = f"{summary['hycean_score']}/100"
    atm = str(summary['atmosphere_detected']) if summary['atmosphere_detected'] is not None else "N/A"
    eta = f"{summary['qhf_eta']:.3f}" if summary['qhf_eta'] is not None else "N/A"
    hab = "✓ Yes" if summary['qhf_habitable'] else ("✗ No" if summary['qhf_habitable'] is not None else "N/A")
    
    print(f"{planet:<20s} {hycean:<10s} {score:<8s} {atm:<8s} {eta:<8s} {hab}")

print("="*70)
print(f"\nProcessed {len(results_summary)}/{len(database['planets'])} planets")
