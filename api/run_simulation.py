import json
import random
import math
import hashlib
import time
from urllib.parse import parse_qs

def generate_simulation_data():
    """Generate mock Kalman filter simulation data for Vercel deployment."""
    
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

def handler(request):
    """Vercel serverless function handler."""
    
    # Create headers for all responses
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
        'Access-Control-Max-Age': '86400',
        'Content-Type': 'application/json'
    }
    
    # Handle CORS preflight
    method = request.get('httpMethod', request.get('method', 'GET'))
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    if method == 'GET':
        try:
            # Set seed for reproducible results (but vary per request)
            seed_string = str(time.time())
            seed = int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16) % (2**32)
            random.seed(seed)
            
            data = generate_simulation_data()
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(data)
            }
            
        except Exception as e:
            error_response = {
                "error": "Simulation failed", 
                "details": str(e)
            }
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps(error_response)
            }
    
    return {
        'statusCode': 405,
        'headers': headers,
        'body': json.dumps({"error": "Method not allowed"})
    }