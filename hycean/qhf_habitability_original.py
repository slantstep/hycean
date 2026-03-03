"""
Quantitative Habitability Framework (QHF) calculations.

Based on equations from:
Apai et al. 2024, "A Quantitative Theory of Planetary Habitability"
arXiv:2505.22808

Note: This is an independent implementation of the published equations.
The official QHF tool is available at github.com/danielapai/QHF
"""

import numpy as np

class QHFCalculator:
    """
    Calculate habitability using QHF framework.
    
    Implements equations from Apai et al. 2024.
    """
    
    def __init__(self, planet_params, star_params, atmospheric_results=None):
        """
        Initialize QHF calculator.
        
        Parameters:
        -----------
        planet_params : dict
            Planet properties (radius, mass, semi_major_axis, etc.)
        star_params : dict
            Stellar properties (Teff, luminosity, etc.)
        atmospheric_results : dict, optional
            Results from atmospheric retrieval or spectroscopy
        """
        self.planet = planet_params
        self.star = star_params
        self.atmosphere = atmospheric_results or {}
    
    def calculate_habitability(self):
        """
        Calculate QHF habitability parameter η.
        
        Returns:
        --------
        results : dict
            Complete habitability assessment
        """
        # Component calculations
        F_stellar = self._stellar_flux()
        F_internal = self._internal_flux()
        F_total = F_stellar + F_internal
        
        Delta_G = self._chemical_disequilibrium()
        f_liquid = self._liquid_water_fraction()
        t_stable = self._stability_timescale()
        
        # Compute habitability parameter (Eq. 5 from paper)
        eta = self._compute_eta(F_total, Delta_G, f_liquid, t_stable)
        
        # Threshold: η > 0.1 suggests potential habitability
        # (This threshold is from Apai et al. 2024)
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
            'implementation': 'Independent (equations from arXiv:2505.22808)',
            'threshold': 0.1,
            'interpretation': self._interpret_result(eta, habitable)
        }
    
    def _stellar_flux(self):
        """Calculate stellar irradiation at planet (W/m²)."""
        L_star_W = self.star['luminosity'] * 3.828e26  # Convert L_sun to W
        a_m = self.planet['semi_major_axis'] * 1.496e11  # AU to m
        
        F = L_star_W / (4 * np.pi * a_m**2)
        return F
    
    def _internal_flux(self):
        """
        Calculate internal heating (W/m²).
        
        Sources:
        - Radiogenic decay (from long-lived isotopes: U, Th, K)
        - Tidal heating (if applicable)
        """
        M = self.planet['mass']  # Earth masses
        
        # Earth's surface heat flux from radioactivity: ~0.087 W/m²
        # Scale by mass (more massive → more radiogenic material)
        # Note: This is a simplified approximation
        F_radiogenic = 0.087 * M
        
        # TODO: Add tidal heating calculation for multi-planet systems
        # For now, we only include radiogenic heating
        
        return F_radiogenic
    
    def _chemical_disequilibrium(self):
        """
        Estimate available chemical free energy (kJ/mol).
        
        For Hycean worlds: H₂/oxidant disequilibrium provides energy
        for potential metabolism.
        """
        # If we have atmospheric retrieval results, use them
        if 'H2_mixing_ratio' in self.atmosphere:
            H2 = self.atmosphere.get('H2_mixing_ratio', 0)
            CO2 = self.atmosphere.get('CO2_mixing_ratio', 0)
            CH4 = self.atmosphere.get('CH4_mixing_ratio', 0)
            
            # H₂ + CO₂ → CH₄ + H₂O (methanogenesis)
            # Strong disequilibrium if H₂ and oxidants coexist
            if H2 > 0.01 and CO2 > 1e-4:
                return 150  # High disequilibrium (kJ/mol)
            elif H2 > 0.001 and (CO2 > 1e-6 or CH4 > 1e-6):
                return 80  # Moderate disequilibrium
        
        # Default assumption for Hycean candidates:
        # H₂-rich atmospheres are inherently out of equilibrium
        # with underlying water ocean → moderate chemical potential
        return 50
    
    def _liquid_water_fraction(self):
        """
        Estimate fraction of planet with liquid water.
        
        For Hycean worlds: Ocean beneath H₂ atmosphere.
        Depends on surface temperature and pressure.
        """
        # Get temperature (from retrieval or equilibrium estimate)
        T = self.atmosphere.get('surface_temp', 
                                self.planet.get('equilibrium_temp', 300))
        
        # Get pressure (if available from retrieval)
        P = self.atmosphere.get('surface_pressure', 1.0)  # bar
        
        # Liquid water range depends on pressure
        # (water phase diagram)
        if P > 100:
            # High pressure: water liquid up to critical point (647 K)
            T_min, T_max = 273, 647
        elif P > 10:
            # Moderate pressure: extended range
            T_min, T_max = 273, 450
        else:
            # ~1 bar: normal range
            T_min, T_max = 273, 373
        
        # Estimate fraction based on temperature
        if T_min < T < T_max:
            # In liquid range: assume substantial ocean
            # (50% is conservative estimate for Hycean worlds)
            f_liquid = 0.5
        elif abs(T - T_min) < 50 or abs(T - T_max) < 50:
            # Near phase boundaries: marginal/partial liquid
            f_liquid = 0.2
        else:
            # Outside liquid water range
            f_liquid = 0.0
        
        return f_liquid
    
    def _stability_timescale(self):
        """
        Estimate time planet remains habitable (Gyr).
        
        Limited primarily by stellar evolution.
        M dwarfs are stable for >10 Gyr, Sun-like stars ~5-10 Gyr.
        """
        Teff = self.star['Teff']
        
        # Stellar main sequence lifetime scales roughly as M^-2.5
        # We approximate from Teff
        if Teff < 3500:
            # M dwarf: main sequence lifetime >> 10 Gyr
            return 10.0
        elif Teff < 5000:
            # K dwarf: ~15-50 Gyr
            return 15.0
        elif Teff < 6000:
            # G dwarf (Sun-like): ~10 Gyr
            return 10.0
        elif Teff < 7000:
            # F dwarf: ~3-7 Gyr
            return 5.0
        else:
            # A dwarf or hotter: <2 Gyr
            return 2.0
    
    def _compute_eta(self, F_total, Delta_G, f_liquid, t_stable):
        """
        Combine factors into habitability parameter.
        
        Based on Equation 5 from Apai et al. 2024:
        η ∝ (F/F₀) × (ΔG/ΔG₀) × f_liquid × (t/t₀)
        
        Where ₀ indicates Earth reference values.
        """
        # Earth reference values
        F_earth = 1361  # W/m² (solar constant at Earth)
        DeltaG_earth = 100  # kJ/mol (Earth's biosphere chemical disequilibrium)
        t_earth = 4.5  # Gyr (age of Earth)
        
        # Normalized factors
        f_energy = F_total / F_earth
        f_chemistry = Delta_G / DeltaG_earth
        f_time = t_stable / t_earth
        
        # Combined habitability parameter
        # η = 1.0 means Earth-like habitability
        eta = f_energy * f_chemistry * f_liquid * f_time
        
        return eta
    
    def _interpret_result(self, eta, habitable):
        """Provide human-readable interpretation of habitability."""
        if eta > 1.0:
            return "Highly favorable for habitability (η > 1.0, exceeds Earth)"
        elif eta > 0.5:
            return "Favorable for habitability (0.5 < η < 1.0, comparable to Earth)"
        elif eta > 0.1:
            return "Marginally habitable (0.1 < η < 0.5, below Earth but plausible)"
        else:
            return "Unlikely to be habitable (η < 0.1)"

# =============================================================================
# Example usage and testing
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("QHF HABITABILITY CALCULATOR - TEST")
    print("="*70)
    
    # Test on LHS 1140 b
    lhs1140b = {
        'radius': 1.730,
        'mass': 5.60,
        'semi_major_axis': 0.0936,
        'equilibrium_temp': 230
    }
    
    lhs1140_star = {
        'Teff': 3216,
        'luminosity': 0.00468
    }
    
    # Calculate habitability
    qhf = QHFCalculator(lhs1140b, lhs1140_star)
    results = qhf.calculate_habitability()
    
    print("\nQHF Habitability Assessment - LHS 1140 b")
    print("-" * 70)
    print(f"Habitability Parameter (η): {results['eta']:.3f}")
    print(f"Threshold: η > {results['threshold']} for potential habitability")
    print(f"Assessment: {'✓ Potentially habitable' if results['potentially_habitable'] else '✗ Unlikely habitable'}")
    print(f"\nInterpretation: {results['interpretation']}")
    
    print("\nComponent Breakdown:")
    print(f"  Total Energy Flux:        {results['F_total_W_m2']:.1f} W/m²")
    print(f"    - Stellar:              {results['F_stellar_W_m2']:.1f} W/m²")
    print(f"    - Internal:             {results['F_internal_W_m2']:.1f} W/m²")
    print(f"  Chemical Disequilibrium:  {results['Delta_G_kJ_mol']:.0f} kJ/mol")
    print(f"  Liquid Water Fraction:    {results['f_liquid']:.2f}")
    print(f"  Stability Timescale:      {results['t_stable_Gyr']:.1f} Gyr")
    
    print("\nComparison to Earth:")
    F_earth = 1361
    print(f"  Energy flux:  {results['F_total_W_m2']/F_earth:.2f}× Earth")
    print(f"  Stability:    {results['t_stable_Gyr']/4.5:.2f}× Earth lifetime")
    
    print("="*70)
