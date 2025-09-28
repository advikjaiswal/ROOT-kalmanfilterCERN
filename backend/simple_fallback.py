#!/usr/bin/env python3
"""
Simple fallback simulation that generates test data without requiring C++ compilation.
This ensures the web application works even if ROOT/C++ compilation fails.
"""

import json
import random
import math

def generate_simulation_data():
    """Generate mock Kalman filter simulation data."""
    
    # Physics parameters
    n_layers = 10
    layer_x_positions = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    measurement_error = 2.0
    
    # Generate true track (simple helical path)
    true_track = []
    initial_y = 5.0
    initial_phi = -0.2
    radius = 100.0  # Radius of curvature
    
    # Fine-grained true track
    for x in range(0, 101, 1):
        y = initial_y + x * math.tan(initial_phi) - (x**2) / (2 * radius)
        true_track.append({"x": x, "y": y})
    
    # Generate hits with measurement errors
    hits = []
    for x_pos in layer_x_positions:
        true_y = initial_y + x_pos * math.tan(initial_phi) - (x_pos**2) / (2 * radius)
        measured_y = true_y + random.gauss(0, measurement_error)
        hits.append({"x": x_pos, "y": measured_y})
    
    # Generate Kalman filter reconstructed track (with some smoothing)
    kf_track = []
    for x_pos in layer_x_positions:
        # Add some reconstruction uncertainty
        true_y = initial_y + x_pos * math.tan(initial_phi) - (x_pos**2) / (2 * radius)
        kf_y = true_y + random.gauss(0, measurement_error * 0.5)  # Better than raw measurements
        kf_track.append({"x": x_pos, "y": kf_y})
    
    return {
        "detector_layers": layer_x_positions,
        "true_track": true_track,
        "hits": hits,
        "kf_track": kf_track
    }

if __name__ == "__main__":
    # Set seed for reproducible results
    random.seed(42)
    data = generate_simulation_data()
    print(json.dumps(data))