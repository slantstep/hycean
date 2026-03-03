"""
Quantitative Habitability Framework (QHF) calculations.

Based on equations from:
Apai et al. 2024, "A Quantitative Theory of Planetary Habitability"
arXiv:2505.22808

Modified to account for optimal energy flux range (not monotonic).
"""

import numpy as np

class QHFCalculator:
    """Calculate habitability using QHF framework."""
    
    def __init__(self, planet_params, star_params, atmospheric_results=None):
        self.planet = planet_params
        self.star = star_params
        self.atmosphere = atmospheric_results or {}
    
    def calculate_habitability(self):
        """Calculate QHF habitability parameter η."""
        # Component calculations
        F_stellar = self._stellar_flux()
        F_internal = self._internal_flux()
        F_total = F_stellar + F_internal
        
        Delta_G = self._chemical_disequilibrium()
        f_liquid = self._liquid_water_fraction()
        t_stable = self._stability_timescale()
        
        # Compute habitability parameter
        eta = self._compute_eta(F_total, Delta_G, f_liquid, t_stable)
        
        # Threshold
        habitable = eta > 0.1
        
        return {
            'eta': float(eta),
            'F_total_W_m2': float(F_total),
            'F_stellar_W_m2': float(F_stellar),
            'F_internal_W_m2': float(F_internal),
            'Delta_G_kJ_mol': float(Delta_G),
            'f_liquid': float(f_liquid),
            't_stable_Gyr': float(t_stable),
            'potentially_habitable': habitable,
            'framework': 'QHF (Apai et al. 2024)',
            'implementation': 'Modified for optimal energy flux range',
            'threshold': 0.1,
            'interpretation': self._interpret_result(eta, habitable)
        }
    
    def _stellar_flux(self):
        """Calculate stellar irradiation at planet (W/m²)."""
        L_star_W = self.star['luminosity'] * 3.828e26
        a_m = self.planet['semi_major_axis'] * 1.496e11
        F = L_star_W / (4 * np.pi * a_m**2)
        return F
    
    def _internal_flux(self):
        """Calculate internal heating (W/m²)."""
        M = self.planet['mass']
        F_radiogenic = 0.087 * M
        return F_radiogenic
    
    def _chemical_disequilibrium(self):
        """Estimate available chemical free energy (kJ/mol)."""
        if 'H2_mixing_ratio' in self.atmosphere:
            H2 = self.atmosphere.get('H2_mixing_ratio', 0)
            CO2 = self.atmosphere.get('CO2_mixing_ratio', 0)
            
            if H2 > 0.01 and CO2 > 1e-4:
                return 150
            elif H2 > 0.001 and CO2 > 1e-6:
                return 80
        
        return 50
    
    def _liquid_water_fraction(self):
        """Estimate fraction of planet with liquid water."""
        T = self.atmosphere.get('surface_temp', 
                                self.planet.get('equilibrium_temp', 300))
        P = self.atmosphere.get('surface_pressure', 1.0)
        
        if P > 100:
            T_min, T_max = 273, 647
        elif P > 10:
            T_min, T_max = 273, 450
        else:
            T_min, T_max = 273, 373
        
        if T_min < T < T_max:
            f_liquid = 0.5
        elif abs(T - T_min) < 50 or abs(T - T_max) < 50:
            f_liquid = 0.2
        else:
            f_liquid = 0.0
        
        return f_liquid
    
    def _stability_timescale(self):
        """Estimate time planet remains habitable (Gyr)."""
        Teff = self.star['Teff']
        
        if Teff < 3500:
            return 10.0
        elif Teff < 5000:
            return 15.0
        elif Teff < 6000:
            return 10.0
        elif Teff < 7000:
            return 5.0
        else:
            return 2.0
    
    def _compute_eta(self, F_total, Delta_G, f_liquid, t_stable):
        """
        Combine factors into habitability parameter.
        
        MODIFIED: Energy flux has optimal range, not monotonic increase.
        """
        # Earth reference values
        F_earth = 1361  # W/m²
        DeltaG_earth = 100  # kJ/mol
        t_earth = 4.5  # Gyr
        
        # === MODIFIED ENERGY FACTOR ===
        # Instead of f_energy = F_total / F_earth (monotonic)
        # Use Gaussian-like function centered on Earth value
        
        # Optimal range: 0.5× to 2× Earth flux
        F_optimal_min = 0.5 * F_earth  # ~680 W/m²
        F_optimal_max = 2.0 * F_earth  # ~2720 W/m²
        
        if F_optimal_min <= F_total <= F_optimal_max:
            # In optimal range: scale linearly to Earth
            f_energy = min(F_total / F_earth, F_earth / F_total)
        elif F_total < F_optimal_min:
            # Too cold: penalize quadratically
            f_energy = (F_total / F_optimal_min)**2
        else:  # F_total > F_optimal_max
            # Too hot: penalize quadratically
            f_energy = (F_optimal_max / F_total)**2
        
        # === ORIGINAL FACTORS ===
        f_chemistry = Delta_G / DeltaG_earth
        f_time = t_stable / t_earth
        
        # Combined habitability parameter
        eta = f_energy * f_chemistry * f_liquid * f_time
        
        return eta
    
    def _interpret_result(self, eta, habitable):
        """Provide human-readable interpretation."""
        if eta > 1.0:
            return "Highly favorable (η > 1.0, exceeds Earth)"
        elif eta > 0.5:
            return "Favorable (0.5 < η < 1.0, comparable to Earth)"
        elif eta > 0.1:
            return "Marginally habitable (0.1 < η < 0.5)"
        else:
            return "Unlikely habitable (η < 0.1)"

# Test
if __name__ == "__main__":
    print("="*70)
    print("QHF HABITABILITY CALCULATOR - REVISED")
    print("="*70)
    
    # Test on LHS 1140 b
    lhs1140b = {'radius': 1.730, 'mass': 5.60, 'semi_major_axis': 0.0936, 'equilibrium_temp': 230}
    lhs1140_star = {'Teff': 3216, 'luminosity': 0.00468}
    
    qhf = QHFCalculator(lhs1140b, lhs1140_star)
    results = qhf.calculate_habitability()
    
    print("\nLHS 1140 b:")
    print(f"  η = {results['eta']:.3f}")
    print(f"  Habitable: {results['potentially_habitable']}")
    print(f"  {results['interpretation']}")
    
    # Test on TOI-270 d (hot Hycean)
    toi270d = {'radius': 2.53, 'mass': 11.9, 'semi_major_axis': 0.0808, 'equilibrium_temp': 350}
    toi270_star = {'Teff': 3506, 'luminosity': 0.0273}
    
    qhf2 = QHFCalculator(toi270d, toi270_star)
    results2 = qhf2.calculate_habitability()
    
    print("\nTOI-270 d:")
    print(f"  η = {results2['eta']:.3f}")
    print(f"  Habitable: {results2['potentially_habitable']}")
    print(f"  {results2['interpretation']}")
    
    # Compare energy flux factors
    print("\nEnergy Analysis:")
    print(f"  LHS 1140 b flux: {results['F_total_W_m2']:.0f} W/m² ({results['F_total_W_m2']/1361:.2f}× Earth)")
    print(f"  TOI-270 d flux:  {results2['F_total_W_m2']:.0f} W/m² ({results2['F_total_W_m2']/1361:.2f}× Earth)")
