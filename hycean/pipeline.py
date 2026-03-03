"""
Main pipeline orchestrator - runs all stages for any planet.
"""

import json
from pathlib import Path
import numpy as np

from hycean.screening import hycean_candidate_screen
from hycean.spectroscopy import SpectrumAnalyzer
from hycean.data_loader import SpectrumLoader
from hycean.qhf_habitability import QHFCalculator
from hycean.utils.data_io import save_results

class HyceanPipeline:
    """Complete Hycean analysis pipeline for any planet."""
    
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        self.planet_name = self.config['name']
        self.results = {}
        
        print(f"Initialized pipeline for {self.planet_name}")
    
    def run_screening(self):
        """Stage 1: Hycean candidate screening."""
        print(f"\n{'='*60}")
        print(f"Stage 1: Hycean Screening - {self.planet_name}")
        print(f"{'='*60}")
        
        planet_params = self.config['planet']
        star_params = self.config['star']
        
        is_candidate, score, reasons = hycean_candidate_screen(
            planet_params, star_params
        )
        
        self.results['screening'] = {
            'is_hycean_candidate': is_candidate,
            'score': score,
            'reasons': reasons
        }
        
        print(f"Hycean Candidate: {is_candidate} (score: {score}/100)")
        for reason in reasons:
            print(f"  • {reason}")
        
        return is_candidate
    
    def run_spectroscopy(self):
        """Stage 2: Transmission spectroscopy analysis."""
        print(f"\n{'='*60}")
        print(f"Stage 2: Spectroscopy Analysis - {self.planet_name}")
        print(f"{'='*60}")
        
        if 'observations' not in self.config:
            print("⚠ No observations configured")
            self.results['spectroscopy'] = {'status': 'no_observations'}
            return None
        
        observations = self.config['observations']
        
        if not isinstance(observations, dict) or 'note' in observations:
            print("⚠ Observation data not yet available")
            self.results['spectroscopy'] = {'status': 'data_pending'}
            return None
        
        # Load all available spectra
        combined_wl, combined_depth, combined_err = [], [], []
        
        for instrument, obs_data in observations.items():
            if not isinstance(obs_data, dict):
                continue
                
            filepath = obs_data.get('spectrum_file')
            if not filepath or not Path(filepath).exists():
                print(f"⚠ Spectrum not found for {instrument}: {filepath}")
                continue
            
            print(f"Loading {instrument}...")
            
            loader = SpectrumLoader()
            
            try:
                wl, depth, err = loader.smart_load(filepath)
                print(f"  ✓ {len(wl)} bins, {wl.min():.2f}-{wl.max():.2f} µm")
                
                combined_wl.extend(wl)
                combined_depth.extend(depth)
                combined_err.extend(err)
            except Exception as e:
                print(f"  ✗ Failed: {e}")
        
        if len(combined_wl) == 0:
            print("✗ No spectra successfully loaded")
            self.results['spectroscopy'] = {'status': 'load_failed'}
            return None
        
        # Sort by wavelength
        sort_idx = np.argsort(combined_wl)
        combined_wl = np.array(combined_wl)[sort_idx]
        combined_depth = np.array(combined_depth)[sort_idx]
        combined_err = np.array(combined_err)[sort_idx]
        
        print(f"\nCombined spectrum: {len(combined_wl)} bins, {combined_wl.min():.2f}-{combined_wl.max():.2f} µm")
        
        # Run analysis
        analyzer = SpectrumAnalyzer(combined_wl, combined_depth, combined_err)
        
        chi2_red, is_flat = analyzer.flat_spectrum_test()
        print(f"\nFlat Spectrum Test:")
        print(f"  χ²_reduced = {chi2_red:.2f}")
        print(f"  Atmosphere detected: {not is_flat}")
        
        alpha, alpha_err, is_rayleigh = analyzer.rayleigh_slope()
        if alpha:
            print(f"\nRayleigh Scattering:")
            print(f"  α = {alpha:.2f} ± {alpha_err:.2f}")
            print(f"  Consistent with scattering: {is_rayleigh}")
        
        features = analyzer.molecular_features()
        print(f"\nMolecular Features:")
        for molecule, result in features.items():
            status = "✓" if result['detected'] else "—"
            print(f"  {status} {molecule:15s}: {result['sigma']:+5.2f}σ")
        
        self.results['spectroscopy'] = {
            'n_wavelength_bins': len(combined_wl),
            'wavelength_range': [float(combined_wl.min()), float(combined_wl.max())],
            'atmosphere_detected': not is_flat,
            'chi2_reduced': float(chi2_red),
            'rayleigh': {
                'alpha': float(alpha) if alpha else None,
                'alpha_error': float(alpha_err) if alpha_err else None,
                'consistent_with_scattering': is_rayleigh
            },
            'molecular_features': {
                k: {'sigma': float(v['sigma']), 'detected': v['detected']} 
                for k, v in features.items()
            }
        }
        
        return self.results['spectroscopy']
    
    def run_qhf_habitability(self):
        """Stage 3: QHF Habitability Assessment."""
        print(f"\n{'='*60}")
        print(f"Stage 3: QHF Habitability - {self.planet_name}")
        print(f"{'='*60}")
        
        qhf = QHFCalculator(
            self.config['planet'],
            self.config['star'],
            self.results.get('spectroscopy', {})
        )
        
        hab_results = qhf.calculate_habitability()
        
        print(f"\nQHF Habitability Parameter: η = {hab_results['eta']:.3f}")
        print(f"  Threshold: η > {hab_results['threshold']} for potential habitability")
        
        if hab_results['potentially_habitable']:
            print(f"  Assessment: ✓ Potentially habitable")
        else:
            print(f"  Assessment: ✗ Unlikely habitable")
        
        print(f"\nInterpretation: {hab_results['interpretation']}")
        
        print(f"\nComponent Breakdown:")
        print(f"  Energy flux:              {hab_results['F_total_W_m2']:.1f} W/m²")
        print(f"  Chemical disequilibrium:  {hab_results['Delta_G_kJ_mol']:.0f} kJ/mol")
        print(f"  Liquid water fraction:    {hab_results['f_liquid']:.2f}")
        print(f"  Stability timescale:      {hab_results['t_stable_Gyr']:.1f} Gyr")
        
        self.results['habitability'] = hab_results
        
        return hab_results
    
    def run_full_pipeline(self, save_output=True):
        """Run complete pipeline: screening + spectroscopy + habitability."""
        print(f"\n{'#'*60}")
        print(f"# HYCEAN PIPELINE: {self.planet_name}")
        print(f"{'#'*60}")
        
        # Stage 1: Screening
        is_candidate = self.run_screening()
        
        # Stage 2: Spectroscopy (if candidate and data available)
        if is_candidate:
            self.run_spectroscopy()
            
            # Stage 3: Habitability (always run for candidates)
            self.run_qhf_habitability()
        else:
            print(f"\n⚠ {self.planet_name} did not pass screening - skipping spectroscopy and habitability")
        
        # Save results
        if save_output:
            output_dir = Path('data/outputs')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            planet_id = self.config.get('id', self.planet_name.lower().replace(' ', '_'))
            output_file = output_dir / f"{planet_id}_results.json"
            
            save_results(self.results, output_file)
            print(f"\n✓ Results saved to {output_file}")
        
        return self.results
