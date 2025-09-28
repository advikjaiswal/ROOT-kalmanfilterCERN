from flask import Flask, jsonify, request
import subprocess
import os
import logging
import sys

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define paths relative to the script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CPP_SOURCE = os.path.join(SCRIPT_DIR, "kalman_filter_track.cpp")
EXECUTABLE = os.path.join(SCRIPT_DIR, "kalman_filter_track")

def compile_cpp_code():
    """
    Compiles the C++ source code using root-config.
    Returns True on success, False on failure.
    """
    logger.info("Starting C++ compilation check...")
    
    if not os.path.exists(CPP_SOURCE):
        error_msg = f"C++ source file not found at: {CPP_SOURCE}"
        logger.error(error_msg)
        return False, error_msg

    # Check if compilation is needed
    if os.path.exists(EXECUTABLE) and os.path.getmtime(EXECUTABLE) > os.path.getmtime(CPP_SOURCE):
        logger.info("Executable is up-to-date.")
        return True, "Executable is up-to-date."

    logger.info("Compiling C++ code...")
    
    # Construct the compilation command using root-config
    try:
        # Change to the script directory for compilation
        original_cwd = os.getcwd()
        os.chdir(SCRIPT_DIR)
        
        root_cflags = subprocess.check_output(["root-config", "--cflags"], 
                                            stderr=subprocess.STDOUT).decode("utf-8").strip()
        root_libs = subprocess.check_output(["root-config", "--libs"], 
                                          stderr=subprocess.STDOUT).decode("utf-8").strip()
        
        # Use absolute paths and proper executable name
        executable_name = os.path.basename(EXECUTABLE)
        source_name = os.path.basename(CPP_SOURCE)
        
        # Try different compilers in order of preference
        compilers = ["clang++", "g++"]
        compile_command = None
        
        for compiler in compilers:
            try:
                # Test if compiler works with basic C++
                test_result = subprocess.run([compiler, "--version"], 
                                           capture_output=True, text=True, check=True)
                compile_command = f"{compiler} -stdlib=libc++ -o {executable_name} {source_name} {root_cflags} {root_libs}"
                logger.info(f"Using compiler: {compiler}")
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        if not compile_command:
            return False, "No suitable C++ compiler found (tried: clang++, g++)"
        
        logger.info(f"Compilation command: {compile_command}")
        
        # Execute the compilation command
        process = subprocess.run(compile_command, shell=True, check=True, 
                               capture_output=True, text=True, cwd=SCRIPT_DIR)
        
        os.chdir(original_cwd)
        logger.info("Compilation successful.")
        return True, "Compilation successful."

    except FileNotFoundError as e:
        os.chdir(original_cwd)
        error_msg = "Error: 'root-config' not found. Make sure ROOT is installed and sourced."
        logger.error(f"{error_msg}: {str(e)}")
        return False, error_msg
    except subprocess.CalledProcessError as e:
        os.chdir(original_cwd)
        error_message = f"Compilation failed with exit code {e.returncode}.\n"
        error_message += f"Stderr: {e.stderr}\n"
        error_message += f"Stdout: {e.stdout}"
        logger.error(f"Compilation failed: {error_message}")
        return False, error_message
    except Exception as e:
        os.chdir(original_cwd)
        error_msg = f"Unexpected error during compilation: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

@app.route('/run_simulation', methods=['GET', 'OPTIONS'])
def run_simulation():
    """
    API endpoint to run the simulation.
    It first ensures the C++ code is compiled, then runs it and returns the JSON output.
    """
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        return response
    
    logger.info("Received simulation request")
    
    # Compile the code first
    success, message = compile_cpp_code()
    if not success:
        logger.error(f"Compilation failed: {message}")
        logger.info("Falling back to Python simulation due to compilation failure")
        return run_fallback_simulation()

    # Run the compiled executable
    try:
        logger.info(f"Running executable: {EXECUTABLE}")
        result = subprocess.run([EXECUTABLE], capture_output=True, text=True, 
                              check=True, cwd=SCRIPT_DIR, timeout=30)
        
        # The C++ program outputs a single JSON string to stdout
        json_output = result.stdout.strip()
        if not json_output:
            logger.error("Executable produced no output")
            return jsonify({"error": "No output from simulation", "details": ""}), 500
            
        logger.info("Simulation completed successfully")
        return app.response_class(response=json_output, status=200, mimetype='application/json')
        
    except subprocess.TimeoutExpired:
        logger.error("Simulation timed out")
        return jsonify({"error": "Simulation timed out", "details": "Process took longer than 30 seconds"}), 500
    except subprocess.CalledProcessError as e:
        logger.error(f"Simulation execution failed: {e.stderr}")
        # Fall back to Python simulation
        logger.info("Falling back to Python simulation")
        return run_fallback_simulation()
    except FileNotFoundError:
        logger.error(f"Executable not found at: {EXECUTABLE}")
        # Fall back to Python simulation
        logger.info("Falling back to Python simulation")
        return run_fallback_simulation()
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        # Fall back to Python simulation
        logger.info("Falling back to Python simulation")
        return run_fallback_simulation()

def run_fallback_simulation():
    """Run the Python fallback simulation when C++ compilation fails."""
    try:
        fallback_script = os.path.join(SCRIPT_DIR, "simple_fallback.py")
        result = subprocess.run([sys.executable, fallback_script], 
                              capture_output=True, text=True, check=True, 
                              cwd=SCRIPT_DIR, timeout=10)
        
        json_output = result.stdout.strip()
        if not json_output:
            return jsonify({"error": "Fallback simulation produced no output", "details": ""}), 500
            
        logger.info("Fallback simulation completed successfully")
        return app.response_class(response=json_output, status=200, mimetype='application/json')
        
    except Exception as e:
        logger.error(f"Fallback simulation failed: {str(e)}")
        return jsonify({"error": "Both C++ and fallback simulations failed", 
                       "details": f"Fallback error: {str(e)}"}), 500


@app.after_request
def after_request(response):
    """Add CORS headers to allow frontend access."""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Max-Age', '86400')  # Cache preflight for 24 hours
    return response

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return jsonify({"error": "Endpoint not found", "details": f"Available endpoint: /run_simulation"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    return jsonify({"error": "Internal server error", "details": "Check server logs for details"}), 500

if __name__ == '__main__':
    logger.info("Starting Kalman Filter Flask server...")
    logger.info(f"Script directory: {SCRIPT_DIR}")
    logger.info(f"C++ source: {CPP_SOURCE}")
    logger.info(f"Executable: {EXECUTABLE}")
    
    # Test compilation on startup
    success, message = compile_cpp_code()
    if success:
        logger.info("Initial compilation check passed")
    else:
        logger.warning(f"Initial compilation check failed: {message}")
    
    try:
        app.run(debug=True, host='127.0.0.1', port=5000)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}")
        sys.exit(1)
