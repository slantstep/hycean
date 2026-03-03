"""Data loading and saving utilities."""
import numpy as np
import json

def load_spectrum(filepath):
    """Load spectrum from ASCII file."""
    data = np.loadtxt(filepath, unpack=True)
    if len(data) == 3:
        return {'wavelength': data[0], 'depth': data[1], 'error': data[2]}
    else:
        raise ValueError(f"Expected 3 columns, got {len(data)}")

def convert_to_native_types(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native_types(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif obj is None or isinstance(obj, (str, int, float)):
        return obj
    else:
        return str(obj)

def save_results(results, filepath):
    """Save analysis results as JSON."""
    # Convert numpy types to native Python types
    results_clean = convert_to_native_types(results)
    
    with open(filepath, 'w') as f:
        json.dump(results_clean, f, indent=2)
