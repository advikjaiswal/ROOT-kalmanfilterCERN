/*
 * ROOT-based Kalman Filter for Particle Track Reconstruction - A Simplified Demo
 *
 * This program simulates a simple 2D particle tracking scenario.
 * 1. Defines a set of parallel detector layers.
 * 2. Simulates a particle's helical trajectory in a constant magnetic field.
 * 3. Generates smeared hits at each detector layer.
 * 4. Implements a basic Kalman Filter to reconstruct the track from the hits.
 * 5. Outputs all data (true path, hits, reconstructed track) as a single JSON object to stdout.
 *
 * Compilation (ensure ROOT is sourced):
 * g++ -o kalman_filter_track kalman_filter_track.cpp `root-config --cflags --libs`
 */

#include <iostream>
#include <vector>
#include <cmath>

#include "TRandom3.h"
#include "TVectorD.h"
#include "TMatrixDSym.h"
#include "TMatrixD.h"

// Use ROOT's SMatrix for fixed-size matrix operations for performance
#include "Math/SMatrix.h"
#include "Math/SVector.h"

// Type definitions for clarity
using SVector2 = ROOT::Math::SVector<double, 2>; // State vector [y, phi]
using SMatrix2x2 = ROOT::Math::SMatrix<double, 2, 2>; // Covariance, etc.

// Detector and Physics Parameters
const int n_layers = 10;
const double layer_x_positions[n_layers] = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100};
const double measurement_error = 2.0; // Measurement smearing (in cm)
const double process_noise_q = 0.01; // Process noise (accounts for multiple scattering)
const double pt = 1.0; // GeV
const double B = 1.0; // Tesla
const double R = (pt * 100) / (0.3 * B); // Radius of curvature in cm

// Helper to propagate state to the next layer
// In this simple model, x is not part of the state vector but the independent variable.
// The state is [y, phi], where phi is the angle of the track.
SVector2 propagate(const SVector2& state_k, double x_k, double x_k1) {
    double y = state_k(0);
    double phi = state_k(1);
    double delta_x = x_k1 - x_k;

    SVector2 next_state;
    // Simple linear propagation for small steps
    next_state(0) = y + delta_x * std::tan(phi);
    next_state(1) = phi - (delta_x / R) / std::cos(phi); // Change in angle for helix projected on xy
    return next_state;
}

// Jacobian of the propagation function F
SMatrix2x2 jacobian_F(const SVector2& state_k, double x_k, double x_k1) {
    double phi = state_k(1);
    double delta_x = x_k1 - x_k;
    
    SMatrix2x2 F;
    F(0, 0) = 1.0;
    F(0, 1) = delta_x * (1.0 + std::tan(phi) * std::tan(phi)); // d(y_k+1)/d(phi_k)
    F(1, 0) = 0.0;
    F(1, 1) = 1.0 - (delta_x/R) * (std::sin(phi) / (std::cos(phi)*std::cos(phi))); // d(phi_k+1)/d(phi_k)
    return F;
}


int main() {
    TRandom3 rng(0); // Seed with 0 for reproducibility

    // --- 1. Ground Truth Simulation ---
    std::vector<double> true_x, true_y;
    SVector2 true_state_initial;
    true_state_initial(0) = 5.0;  // Initial y position
    true_state_initial(1) = -0.2; // Initial angle phi
    
    SVector2 current_true_state = true_state_initial;
    double last_x = 0.0;

    for (int i = 0; i < n_layers; ++i) {
        double current_x = layer_x_positions[i];
        for (double x_step = last_x; x_step < current_x; x_step += 0.5) {
            current_true_state = propagate(current_true_state, x_step, x_step + 0.5);
            true_x.push_back(x_step + 0.5);
            true_y.push_back(current_true_state(0));
        }
        last_x = current_x;
    }
    
    // --- 2. Simulate Measurements ---
    std::vector<double> measured_y;
    current_true_state = true_state_initial;
    last_x = 0;
    for (int i = 0; i < n_layers; ++i) {
        double current_x = layer_x_positions[i];
        current_true_state = propagate(current_true_state, last_x, current_x);
        double y_smeared = current_true_state(0) + rng.Gaus(0, measurement_error);
        measured_y.push_back(y_smeared);
        last_x = current_x;
    }

    // --- 3. Kalman Filter Implementation ---
    std::vector<double> kf_x, kf_y;

    // Initial state guess and covariance
    SVector2 x_est = true_state_initial; // Start with a good guess for simplicity
    x_est(0) += rng.Gaus(0, 5.0); // Smear initial guess
    x_est(1) += rng.Gaus(0, 0.1);

    SMatrix2x2 P_est; // Covariance matrix
    P_est(0, 0) = 100.0; // Large initial uncertainty in y
    P_est(1, 1) = 1.0;   // Large initial uncertainty in phi

    // Measurement matrix H (we only measure y)
    ROOT::Math::SMatrix<double, 1, 2> H;
    H(0, 0) = 1.0;
    H(0, 1) = 0.0;

    // Measurement noise covariance R
    ROOT::Math::SMatrix<double, 1, 1> R_matrix;
    R_matrix(0, 0) = measurement_error * measurement_error;
    
    // Process noise covariance Q
    SMatrix2x2 Q;
    Q(0,0) = 0.0;
    Q(1,1) = process_noise_q; // Uncertainty in angle propagation


    double last_kf_x = 0.0;
    for (int i = 0; i < n_layers; ++i) {
        // --- Prediction step ---
        SMatrix2x2 F = jacobian_F(x_est, last_kf_x, layer_x_positions[i]);
        SVector2 x_pred = propagate(x_est, last_kf_x, layer_x_positions[i]);
        SMatrix2x2 P_pred = F * P_est * ROOT::Math::Transpose(F) + Q;

        // --- Update step ---
        ROOT::Math::SVector<double,1> y_residual = ROOT::Math::SVector<double,1>(measured_y[i]) - H * x_pred;
        
        ROOT::Math::SMatrix<double, 1, 1> S = H * P_pred * ROOT::Math::Transpose(H) + R_matrix;
        ROOT::Math::SMatrix<double, 1, 1> S_inv;
        S.Invert(S_inv);

        ROOT::Math::SMatrix<double, 2, 1> K = P_pred * ROOT::Math::Transpose(H) * S_inv; // Kalman Gain
        
        x_est = x_pred + K * y_residual;
        P_est = (ROOT::Math::SMatrixIdentity() - K * H) * P_pred;
        
        kf_x.push_back(layer_x_positions[i]);
        kf_y.push_back(x_est(0));
        last_kf_x = layer_x_positions[i];
    }

    // --- 4. Generate JSON Output ---
    std::cout << "{";
    // Detector geometry
    std::cout << "\"detector_layers\": [";
    for(int i = 0; i < n_layers; ++i) {
        std::cout << layer_x_positions[i] << (i == n_layers - 1 ? "" : ",");
    }
    std::cout << "],";

    // True trajectory
    std::cout << "\"true_track\": [";
    for(size_t i = 0; i < true_x.size(); ++i) {
        std::cout << "{\"x\": " << true_x[i] << ", \"y\": " << true_y[i] << "}" << (i == true_x.size() - 1 ? "" : ",");
    }
    std::cout << "],";
    
    // Simulated hits
    std::cout << "\"hits\": [";
    for(int i = 0; i < n_layers; ++i) {
        std::cout << "{\"x\": " << layer_x_positions[i] << ", \"y\": " << measured_y[i] << "}" << (i == n_layers - 1 ? "" : ",");
    }
    std::cout << "],";

    // Reconstructed Kalman Filter track
    std::cout << "\"kf_track\": [";
    for(size_t i = 0; i < kf_x.size(); ++i) {
        std::cout << "{\"x\": " << kf_x[i] << ", \"y\": " << kf_y[i] << "}" << (i == kf_x.size() - 1 ? "" : ",");
    }
    std::cout << "]";

    std::cout << "}" << std::endl;

    return 0;
}
