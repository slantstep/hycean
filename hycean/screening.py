"""
Stage 1: Hycean Candidate Screening from Archival Data
"""
import numpy as np

def compute_density(mass_earth, radius_earth):
    """Compute bulk density in g/cm³."""
    mass_g = mass_earth * 5.972e27
    radius_cm = radius_earth * 6.371e8
    volume_cm3 = (4/3) * np.pi * radius_cm**3
    return mass_g / volume_cm3

def compute_equilibrium_temp(star_params, semi_major_axis_au, albedo=0.3):
    """Compute equilibrium temperature in K."""
    L_star = star_params['luminosity']
    a_m = semi_major_axis_au * 1.496e11
    T_eq = 279 * (L_star**0.25) * ((1 - albedo)**0.25) / (a_m / 1.496e11)**0.5
    return T_eq

def hycean_candidate_screen(planet_params, star_params):
    """
    Assess if planet meets Hycean criteria.
    
    Parameters:
    -----------
    planet_params : dict
        {'radius': R_earth, 'mass': M_earth, 'period': days, ...}
    star_params : dict
        {'Teff': K, 'radius': R_sun, 'luminosity': L_sun, ...}
    
    Returns:
    --------
    is_candidate : bool
    score : float (0-100)
    reasons : list of str
    """
    score = 0
    reasons = []
    
    # Criterion 1: Size (25 points)
    R = planet_params['radius']
    if 1.5 < R < 2.8:  # Expanded upper limit slightly
        score += 25
        reasons.append(f"Radius {R:.2f} R_Earth in Hycean range")
    elif 1.2 < R < 1.5:
        score += 15
        reasons.append(f"Radius {R:.2f} R_Earth (small Hycean candidate)")
    
    # Criterion 2: Density (25 points)
    if 'mass' in planet_params and planet_params['mass'] is not None:
        rho = compute_density(planet_params['mass'], R)
        if rho < 4.0:
            score += 25
            reasons.append(f"Low density {rho:.1f} g/cm³ suggests volatiles")
        elif rho < 5.0:
            score += 15
            reasons.append(f"Moderate density {rho:.1f} g/cm³")
    
    # Criterion 3: Temperature (30 points) - EXPANDED RANGE
    a_au = planet_params.get('semi_major_axis')
    if a_au:
        T_eq = compute_equilibrium_temp(star_params, a_au)
        
        if 200 < T_eq < 350:
            # Temperate Hycean (most favorable)
            score += 30
            reasons.append(f"Temperate Hycean (T_eq={T_eq:.0f} K)")
        elif 350 <= T_eq < 500:
            # Hot Hycean (still viable)
            score += 25
            reasons.append(f"Hot Hycean (T_eq={T_eq:.0f} K)")
        elif 100 < T_eq <= 200:
            # Cold Hycean
            score += 20
            reasons.append(f"Cold Hycean candidate (T_eq={T_eq:.0f} K)")
        elif T_eq >= 500:
            # Too hot - penalize
            score += 5
            reasons.append(f"Very hot (T_eq={T_eq:.0f} K) - marginal")
    
    # Criterion 4: Stellar type (20 points)
    if star_params['Teff'] < 3900:
        score += 20
        reasons.append("M dwarf host (optimal for spectroscopy)")
    elif star_params['Teff'] < 5300:
        score += 15
        reasons.append("K dwarf host (good for spectroscopy)")
    elif star_params['Teff'] < 6000:
        score += 10
        reasons.append("G dwarf host (moderate spectroscopy signal)")
    elif star_params['Teff'] < 7300:
        score += 5
        reasons.append("F dwarf host")
    
    # Threshold: 50 points to be considered candidate
    return score >= 50, score, reasons

# Example usage
if __name__ == "__main__":
    # Test with TOI-270 d (should now pass)
    toi270d = {
        'radius': 2.53,
        'mass': 11.9,
        'period': 11.38,
        'semi_major_axis': 0.0808
    }
    toi270_star = {
        'Teff': 3506,
        'radius': 0.384,
        'luminosity': 0.0273
    }
    
    is_cand, score, reasons = hycean_candidate_screen(toi270d, toi270_star)
    print(f"TOI-270 d Hycean Candidate: {is_cand} (score: {score})")
    for r in reasons:
        print(f"  - {r}")
