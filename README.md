ROOT-based Kalman Filter Web Demo
An interactive web application demonstrating particle track reconstruction using a Kalman Filter implemented in C++ with the CERN ROOT framework. The C++ backend is served via a Python API, and the visualization is rendered in the browser using React and D3.js.

This project is designed as a portfolio piece to showcase skills in scientific computing, physics simulation, and modern full-stack web development.

🚀 Live Demo
[Link to Your Deployed Application Here]

✨ Key Features
Backend Simulation: Uses C++ and ROOT for a robust and performant physics simulation.

Kalman Filter: Implements a simplified Kalman Filter to reconstruct a particle's trajectory from simulated detector hits.

REST API: A lightweight Python Flask wrapper exposes the C++ simulation as a simple API endpoint.

Interactive Visualization: A React and D3.js frontend provides a clear and interactive display of the detector, true particle path, smeared hits, and the final reconstructed track.

Deployable: Designed for easy deployment on modern serverless platforms like Vercel or Netlify.

🏗️ Architecture
The application follows a decoupled frontend-backend architecture, making it scalable and easy to manage.

Frontend (Client-Side):

A static index.html file containing a React application.

When the user clicks "Run New Simulation," it makes an API call to the backend.

It uses D3.js to dynamically render the received JSON data into an SVG visualization.

Backend (Server-Side API):

A Python Flask application (main.py) acts as a web server.

It exposes a single endpoint (e.g., /api/run_simulation).

This server is the "glue" that allows the web frontend to communicate with the compiled C++ code.

Simulation Core (Executed by Backend):

A C++ program (kalman_filter_track.cpp) that uses the ROOT framework.

The Flask server compiles and executes this program for each API request.

The C++ program performs the simulation and prints the resulting track data as a JSON string to standard output, which is then captured by the Python wrapper and sent to the frontend.

💻 Technology Stack
Simulation: C++, ROOT Framework

Backend: Python, Flask

Frontend: React, D3.js, Tailwind CSS

Deployment: Vercel / Netlify / Docker

🛠️ How to Run Locally
Prerequisites

CERN ROOT: A working installation of ROOT is required. Make sure the root-config command is available in your PATH.

Don't forget to source the setup script: source /path/to/your/root/installation/bin/thisroot.sh

C++ Compiler: A modern C++ compiler like g++ or clang++.

Python: Python 3.7+ with pip.

Step-by-Step Instructions

Clone the Repository

git clone [your-repository-url]
cd kalman-filter-web-demo

Set Up the Backend

Navigate to the backend directory:

cd backend

Install Flask:

pip install Flask

Run the server:

python3 main.py

The server will start on http://127.0.0.1:5000. The first time you run it, it will automatically compile the C++ code into an executable file within the backend directory.

Run the Frontend

In a new terminal, navigate back to the project's root directory.

Open the index.html file directly in your web browser.

On macOS: open index.html

On Linux: xdg-open index.html

On Windows: start index.html

Interact with the Demo

Click the "Run New Simulation" button. The frontend will call your local backend server, fetch the new track data, and update the visualization.

☁️ Deployment to Vercel
This project can be deployed as a serverless application on Vercel. This requires a specific folder structure and configuration.

1. Restructure the Project

Vercel requires serverless functions to be in an api directory at the project root.

/ (root)
├── api/
│   ├── kalman_filter_track.cpp
│   └── index.py             (renamed from main.py)
│
├── index.html
├── requirements.txt
└── vercel.json

Create an api folder in the root.

Move kalman_filter_track.cpp into api/.

Move main.py into api/ and rename it to index.py.

Keep index.html in the root.

2. Create Configuration Files

requirements.txt (in the root directory):

Flask

vercel.json (in the root directory): This file tells Vercel how to build and route your project.

{
  "builds": [
    {
      "src": "/api/index.py",
      "use": "@vercel/python"
    },
    {
      "src": "index.html",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}

3. Update API Endpoint in Frontend

In index.html, change the API_URL constant to point to the Vercel serverless function:

// Change this line in index.html
const API_URL = '/api/run_simulation';

4. Deploy

Install the Vercel CLI: npm install -g vercel

Run the deployment command from your project's root directory:

vercel

Follow the CLI prompts to link and deploy your project.

Important Note on ROOT in Serverless Environments: Standard Vercel build environments do not include the large set of dependencies required by ROOT. A successful deployment may require using a custom Docker container runtime on a platform like Google Cloud Run or AWS Lambda. The setup above is the standard for Python, but the root-config command will likely fail. For a portfolio, demonstrating the working local version and the deployment configuration is often sufficient to prove capability.

📂 Project Structure
kalman-filter-web-demo/
│
├── backend/                  # Contains all backend code
│   │
│   ├── kalman_filter_track.cpp # C++/ROOT simulation core
│   └── main.py                 # Python Flask API wrapper
│
├── index.html                # Frontend React/D3.js application
│
└── README.md                 # Project documentation

🌟 Future Improvements
[ ] Allow user to change parameters (e.g., magnetic field, particle momentum) from the frontend.

[ ] Implement a 3D visualization using Three.js.

[ ] Add more complex physics, such as multiple scattering effects modeled more accurately in the process noise.

[ ] Containerize the backend with Docker for more portable and robust deployment.

📄 License
This project is licensed under the MIT License. See the LICENSE.md file for details.