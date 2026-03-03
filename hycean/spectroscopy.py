"""
Stage 2: Transmission Spectroscopy Analysis
"""
import numpy as np
from scipy.stats import linregress
from scipy.optimize import curve_fit
from numpy.polynomial import Polynomial

class SpectrumAnalyzer:
    """Analyze transmission spectra with model-independent tests."""
    
    def __init__(self, wavelength, depth, error):
        """
        Parameters:
        -----------
        wavelength : array, µm
        depth : array, ppm or fraction
        error : array, same units as depth
        """
        self.wl = np.array(wavelength)
        self.depth = np.array(depth)
        self.error = np.array(error)
    
    def flat_spectrum_test(self, poly_order=2):
        """
        Test if spectrum is consistent with flat (no atmosphere).
        
        Returns:
        --------
        chi2_reduced : float
        is_flat : bool (True if consistent with flat)
        """
        # Fit polynomial baseline
        p = Polynomial.fit(self.wl, self.depth, poly_order, w=1/self.error)
        baseline = p(self.wl)
        
        # Compute chi-squared
        residuals = self.depth - baseline
        chi2 = np.sum((residuals / self.error)**2)
        dof = len(self.wl) - (poly_order + 1)
        chi2_red = chi2 / dof
        
        return chi2_red, chi2_red < 1.5
    
    def rayleigh_slope(self, wl_max=1.5):
        """
        Fit power law to short wavelengths.
        
        Returns:
        --------
        alpha : float (expected -4 for Rayleigh)
        alpha_error : float
        is_rayleigh : bool
        """
        mask = self.wl < wl_max
        if np.sum(mask) < 5:
            return None, None, False
        
        def power_law(wl, D0, A, alpha):
            return D0 + A * (wl / 1.0)**alpha
        
        try:
            popt, pcov = curve_fit(
                power_law,
                self.wl[mask],
                self.depth[mask],
                sigma=self.error[mask],
                p0=[np.mean(self.depth), 500, -4]
            )
            alpha = popt[2]
            alpha_err = np.sqrt(pcov[2, 2])
            
            # Consistent if within 2σ of -4
            is_rayleigh = abs(alpha - (-4)) < 2 * alpha_err
            
            return alpha, alpha_err, is_rayleigh
            
        except:
            return None, None, False
    
    def molecular_features(self):
        """
        Search for molecular absorption bands.
        
        Returns:
        --------
        dict : {molecule: {'sigma': float, 'detected': bool}}
        """
        features = {
            'H2O_1.4um': (1.3, 1.5),
            'H2O_1.9um': (1.8, 2.0),
            'CO2_2.7um': (2.6, 2.8),
            'CH4_2.3um': (2.2, 2.4),
            'CO2_4.3um': (4.2, 4.4),
        }
        
        results = {}
        for name, (wl_min, wl_max) in features.items():
            mask = (self.wl >= wl_min) & (self.wl <= wl_max)
            if np.sum(mask) < 3:
                continue
            
            feature_depth = self.depth[mask]
            continuum = np.mean(self.depth[mask])
            
            absorption = feature_depth - continuum
            t_stat = np.mean(absorption) / (np.std(absorption) / np.sqrt(len(absorption)))
            
            results[name] = {
                'sigma': t_stat,
                'detected': abs(t_stat) > 3
            }
        
        return results

# Example usage
if __name__ == "__main__":
    # Dummy data
    wl = np.linspace(0.6, 5.0, 100)
    depth = 5500 + 200 * (wl / 1.0)**(-4) + np.random.normal(0, 50, 100)
    error = np.ones(100) * 50
    
    analyzer = SpectrumAnalyzer(wl, depth, error)
    
    chi2, is_flat = analyzer.flat_spectrum_test()
    print(f"Flat test: χ²_red = {chi2:.2f}, flat = {is_flat}")
    
    alpha, alpha_err, is_rayleigh = analyzer.rayleigh_slope()
    if alpha:
        print(f"Rayleigh: α = {alpha:.2f} ± {alpha_err:.2f}, consistent = {is_rayleigh}")
