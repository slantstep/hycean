"""
Flexible data loading for different spectrum formats.
"""

import numpy as np
from pathlib import Path

class SpectrumLoader:
    """Load spectra from various file formats."""
    
    @staticmethod
    def load_cadieux_format(filepath):
        """Load Cadieux+2024 NIRISS format (machine-readable table)."""
        data = np.loadtxt(filepath, skiprows=21, unpack=True)
        wl = data[0]
        depth = data[2]  # planet b
        err = data[3]
        return wl, depth, err
    
    @staticmethod
    def load_damiano_format(filepath):
        """Load Damiano+2024 NIRSpec format (2 detectors side-by-side)."""
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        data_lines = lines[7:]  # Skip header
        
        nrs1_wl, nrs1_depth, nrs1_err = [], [], []
        nrs2_wl, nrs2_depth, nrs2_err = [], [], []
        
        for line in data_lines:
            parts = line.split()
            if len(parts) >= 6:
                wl_range = parts[0].split('-')
                nrs1_wl.append((float(wl_range[0]) + float(wl_range[1])) / 2)
                nrs1_depth.append(float(parts[1]))
                nrs1_err.append(float(parts[2]))
                
                wl_range = parts[3].split('-')
                nrs2_wl.append((float(wl_range[0]) + float(wl_range[1])) / 2)
                nrs2_depth.append(float(parts[4]))
                nrs2_err.append(float(parts[5]))
            elif len(parts) == 3:
                wl_range = parts[0].split('-')
                nrs2_wl.append((float(wl_range[0]) + float(wl_range[1])) / 2)
                nrs2_depth.append(float(parts[1]))
                nrs2_err.append(float(parts[2]))
        
        wl = np.array(nrs1_wl + nrs2_wl)
        depth = np.array(nrs1_depth + nrs2_depth)
        err = np.array(nrs1_err + nrs2_err)
        
        return wl, depth, err
    
    @staticmethod
    def load_simple_spectrum(filepath, skiprows=0):
        """Load simple 3-column format: wavelength, depth, error."""
        data = np.loadtxt(filepath, skiprows=skiprows, unpack=True)
        
        if len(data) == 3:
            wl, depth, error = data
            
            # Convert to ppm if in fraction
            if np.median(depth) < 0.1:
                depth *= 1e6
                error *= 1e6
            
            return wl, depth, error
        else:
            raise ValueError(f"Expected 3 columns, got {len(data)}")
    
    @classmethod
    def smart_load(cls, filepath, format_hint=None):
        """
        Intelligently load spectrum, auto-detecting format.
        
        Parameters:
        -----------
        filepath : str or Path
        format_hint : str, optional
            'damiano', 'cadieux', 'simple', or None
        
        Returns:
        --------
        wl, depth, error : arrays in µm, ppm, ppm
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Spectrum file not found: {filepath}")
        
        # Check filename for hints
        filename = filepath.name.lower()
        
        if 'cadieux' in filename or 'niriss' in filename:
            format_hint = 'cadieux'
        elif 'damiano' in filename or 'nirspec' in filename:
            format_hint = 'damiano'
        
        # Use hint
        if format_hint == 'damiano':
            return cls.load_damiano_format(filepath)
        elif format_hint == 'cadieux':
            return cls.load_cadieux_format(filepath)
        elif format_hint == 'simple':
            return cls.load_simple_spectrum(filepath)
        
        # Try to auto-detect by reading first line
        with open(filepath, 'r') as f:
            first_line = f.readline().strip()
        
        if first_line.startswith('Title:'):
            return cls.load_cadieux_format(filepath)
        elif first_line.startswith('Table'):
            return cls.load_damiano_format(filepath)
        else:
            # Count comment lines
            skiprows = 0
            with open(filepath, 'r') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        skiprows += 1
                    else:
                        break
            return cls.load_simple_spectrum(filepath, skiprows=skiprows)
