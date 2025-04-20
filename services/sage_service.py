"""
Sage Service Module

This module provides functionality to interact with SageMath through a Docker container.
"""
import requests
import logging
import os
import json
import re
import time
import math
import uuid
import websocket
import threading
import queue
import hmac
import hashlib
import base64
from datetime import datetime

class SageService:
    """Service for executing SageMath code via a Docker container"""
    
    def __init__(self, url=None):
        """
        Initialize the SageMath service
        
        Args:
            url (str): URL of the SageMath service endpoint. 
                       If None, will check SAGE_URL environment variable or use default.
        """
        # Allow configuration through environment variable
        self.base_url = url or os.environ.get('SAGE_URL', "http://127.0.0.1:8888")
        # Try to get the token from environment or use the token from your Docker container
        self.token = os.environ.get('JUPYTER_TOKEN', "dd0bf3e49f444c87dbe508db1897787df07e76e6c4a37ca1")
        self.logger = logging.getLogger(__name__)
        self.available = False
        self.kernel_id = None
        self.session_id = None
        self.auth_attempts = 0  # Track authentication attempts to prevent infinite loops
        
        # Log the connection details for debugging
        self.logger.info(f"Attempting to connect to SageMath at {self.base_url} with token {self.token[:5]}...")
        
        # Only try to check availability if we have a token
        if self.token:
            self.available = self._check_availability()
        else:
            self.logger.warning("No Jupyter token available, SageMath service will be disabled")
            
        # Log the availability status
        if self.available:
            self.logger.info(f"SageMath service is available at {self.base_url}")
        else:
            self.logger.warning(
                f"SageMath service is not available at {self.base_url}. "
                "Some advanced mathematical operations may not work. "
                "Check README.md for information on setting up SageMath."
            )
    
    def _check_availability(self):
        """Check if the SageMath service is available"""
        # Prevent infinite loops by limiting auth attempts
        if self.auth_attempts >= 2:
            self.logger.warning("Too many authentication attempts, disabling SageMath service")
            return False
            
        self.auth_attempts += 1
        
        try:
            # Try to access the Jupyter API with the token
            params = {}
            if self.token:
                params["token"] = self.token
                
            response = requests.get(
                f"{self.base_url}/api/kernels", 
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                # API is accessible, look for existing kernels
                kernels = response.json()
                if kernels:
                    # Use the first available kernel
                    self.kernel_id = kernels[0].get('id')
                    self.logger.info(f"Found existing kernel with ID: {self.kernel_id}")
                    return True
                else:
                    # Try to create a new kernel
                    return self._create_kernel()
            elif response.status_code == 403:
                self.logger.warning("Authentication failed with provided token")
                return False
            else:
                self.logger.warning(f"Jupyter API returned status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.warning(f"Error checking SageMath availability: {str(e)}")
            return False
    
    def _create_kernel(self):
        """Create a new Jupyter kernel"""
        if self.auth_attempts >= 2:
            self.logger.warning("Too many authentication attempts, disabling SageMath service")
            return False
            
        try:
            headers = {"Content-Type": "application/json"}
            params = {}
            if self.token:
                params["token"] = self.token
                
            # Create a new kernel
            response = requests.post(
                f"{self.base_url}/api/kernels",
                headers=headers,
                params=params,
                json={}
            )
            
            if response.status_code == 201:
                kernel_info = response.json()
                self.kernel_id = kernel_info.get('id')
                self.logger.info(f"Created new kernel with ID: {self.kernel_id}")
                return True
            else:
                self.logger.warning(f"Failed to create kernel. Status code: {response.status_code}")
                self.logger.warning(f"Response content: {response.text}")
                
                # If it's a 403 error, the token might be wrong or missing
                if response.status_code == 403:
                    self.logger.warning("Authorization failed. Check the Jupyter token.")
                    return False
                    
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating kernel: {str(e)}")
            return False
    
    def execute(self, code):
        """
        Execute SageMath code using Jupyter kernel
        
        Args:
            code (str): SageMath code to execute
            
        Returns:
            dict: Result of executing the code
        """
        if not self.available or not self.kernel_id:
            raise RuntimeError("SageMath Jupyter service is not available")
        
        try:
            # Check if the kernel is still alive, recreate if needed
            self._check_kernel_alive()
            
            # First, try to use the notebook-based execution since that works reliably
            # This is better than hard-coding special cases
            try:
                return self._execute_via_notebook(code)
            except Exception as notebook_error:
                self.logger.warning(f"Notebook execution failed: {str(notebook_error)}")
                
                # Fall back to WebSocket communication
                try:
                    return self._execute_via_websocket(code)
                except Exception as ws_error:
                    self.logger.warning(f"WebSocket execution failed: {str(ws_error)}")
                    
                    # Last resort - create temporary files for execution
                    return self._execute_via_temp_file(code)
        except Exception as e:
            self.logger.error(f"Error executing SageMath code: {str(e)}")
            # Return a descriptive error rather than silently failing
            return {"stdout": f"Error executing code: {str(e)}", "error": True}
    
    def _execute_via_notebook(self, code):
        """Execute code by creating a temporary notebook"""
        self.logger.info("Executing code via notebook creation")
        
        headers = {"Content-Type": "application/json"}
        params = {}
        if self.token:
            params["token"] = self.token
            
        # Create a temporary notebook
        notebook_name = f"temp_{int(time.time())}.ipynb"
        
        try:
            # Create notebook with the code
            response = requests.post(
                f"{self.base_url}/api/contents",
                headers=headers,
                params=params,
                json={
                    "type": "notebook",
                    "path": notebook_name,
                    "format": "json",
                    "content": {
                        "metadata": {
                            "kernelspec": {
                                "name": "python3",
                                "display_name": "Python 3"
                            }
                        },
                        "nbformat": 4,
                        "nbformat_minor": 5,
                        "cells": [
                            {
                                "cell_type": "code",
                                "execution_count": None,
                                "metadata": {},
                                "source": code,
                                "outputs": []
                            }
                        ]
                    }
                }
            )
            
            if response.status_code != 201:
                raise Exception(f"Failed to create notebook: {response.status_code}, Response: {response.text}")
                
            notebook_path = response.json().get("path", notebook_name)
            self.logger.info(f"Created notebook at: {notebook_path}")
            
            # Execute the cell using the sessions API
            session_response = requests.post(
                f"{self.base_url}/api/sessions",
                headers=headers,
                params=params,
                json={
                    "path": notebook_path,
                    "type": "notebook",
                    "name": "",
                    "kernel": {
                        "id": self.kernel_id,
                        "name": "python3"
                    }
                }
            )
            
            if session_response.status_code not in (200, 201):
                self.logger.warning(f"Failed to create session: {session_response.status_code}")
            else:
                session_id = session_response.json().get("id")
                self.logger.info(f"Created session with ID: {session_id}")
            
            # Wait for execution
            time.sleep(3)
            
            # Retrieve the notebook with outputs
            get_response = requests.get(
                f"{self.base_url}/api/contents/{notebook_path}",
                headers=headers,
                params=params
            )
            
            outputs = []
            if get_response.status_code == 200:
                notebook_data = get_response.json()
                cells = notebook_data.get("content", {}).get("cells", [])
                
                for cell in cells:
                    if cell.get("cell_type") == "code":
                        for cell_output in cell.get("outputs", []):
                            if "text" in cell_output:
                                outputs.append(cell_output["text"])
                            elif "data" in cell_output:
                                if "text/plain" in cell_output["data"]:
                                    outputs.append(cell_output["data"]["text/plain"])
            
            # Clean up the notebook
            try:
                delete_response = requests.delete(
                    f"{self.base_url}/api/contents/{notebook_path}",
                    params=params
                )
                self.logger.info(f"Deleted notebook {notebook_path}: {delete_response.status_code}")
            except Exception as delete_error:
                self.logger.warning(f"Failed to delete notebook: {str(delete_error)}")
            
            # Process outputs to match expected format
            result = "\n".join(outputs)
            if result:
                # Check for Fourier series results
                if "fourier" in code.lower():
                    # Extract LaTeX if available
                    latex_result = None
                    for line in result.split("\n"):
                        if "\\sum" in line or "\\frac" in line:
                            latex_result = line
                            break
                    
                    if latex_result:
                        return {"stdout": f"RESULT: {result}\nLATEX: {latex_result}"}
                
                # Check for Laplace transform results
                if "laplace" in code.lower():
                    # Extract LaTeX if available
                    latex_result = None
                    for line in result.split("\n"):
                        if "\\frac" in line or "e^{" in line:
                            latex_result = line
                            break
                    
                    if latex_result:
                        return {"stdout": f"RESULT: {result}\nLATEX: {latex_result}"}
                
                return {"stdout": result}
            else:
                return {"stdout": f"# No output captured for notebook execution", "error": True}
                
        except Exception as e:
            self.logger.error(f"Error in notebook execution: {str(e)}")
            raise e
    
    def _execute_via_websocket(self, code):
        """Execute code via WebSocket communication with the kernel"""
        self.logger.info("Executing code via WebSocket")
        
        # Generate a message ID
        msg_id = str(uuid.uuid4())
        
        # Create a message queue for the response
        msg_queue = queue.Queue()
        
        # Prepare the WebSocket URL
        ws_url = f"{self.base_url.replace('http://', 'ws://')}/api/kernels/{self.kernel_id}/channels?token={self.token}"
        
        # Define the message handler
        def on_message(ws, message):
            msg_data = json.loads(message)
            if 'parent_header' in msg_data and msg_data['parent_header'].get('msg_id') == msg_id:
                if msg_data['msg_type'] in ('execute_result', 'stream', 'display_data', 'error'):
                    msg_queue.put(msg_data)
        
        # Set up WebSocket connection
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message
        )
        
        # Start WebSocket connection in a separate thread
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Wait for connection to establish
        time.sleep(1)
        
        # Prepare execute message
        execute_msg = {
            'header': {
                'msg_id': msg_id,
                'username': 'sage_service',
                'session': str(uuid.uuid4()),
                'msg_type': 'execute_request',
                'version': '5.2'
            },
            'parent_header': {},
            'metadata': {},
            'content': {
                'code': code,
                'silent': False,
                'store_history': False,
                'user_expressions': {},
                'allow_stdin': False
            }
        }
        
        # Send the message
        ws.send(json.dumps(execute_msg))
        
        # Wait for results
        outputs = []
        try:
            timeout = time.time() + 10  # 10 second timeout
            while time.time() < timeout:
                try:
                    msg = msg_queue.get(timeout=0.1)
                    
                    # Process different message types
                    if msg['msg_type'] == 'execute_result':
                        if 'data' in msg['content']:
                            if 'text/plain' in msg['content']['data']:
                                outputs.append(msg['content']['data']['text/plain'])
                    elif msg['msg_type'] == 'stream':
                        if 'text' in msg['content']:
                            outputs.append(msg['content']['text'])
                    elif msg['msg_type'] == 'error':
                        error_msg = f"Error: {msg['content']['ename']}: {msg['content']['evalue']}"
                        outputs.append(error_msg)
                        break
                    
                    # Check for end of execution
                    if msg['msg_type'] == 'status' and msg['content']['execution_state'] == 'idle':
                        break
                        
                except queue.Empty:
                    continue
        finally:
            # Close WebSocket connection
            ws.close()
        
        # Process outputs
        result = "\n".join(outputs)
        if result:
            return {"stdout": result}
        else:
            raise Exception("No output received from WebSocket execution")
    
    def _execute_via_temp_file(self, code):
        """Execute code via temporary file creation (last resort)"""
        self.logger.info("Executing code via temporary file")
        
        # Prepare code to capture output
        wrapped_code = """
import sys, io
old_stdout = sys.stdout
new_stdout = io.StringIO()
sys.stdout = new_stdout
try:
    {0}
    # Print special markers for result extraction
    if 'result' in locals():
        print("RESULT_MARKER:", result)
        if hasattr(result, '_latex_'):
            print("LATEX_MARKER:", result._latex_())
except Exception as e:
    print("ERROR_MARKER:", str(e))
finally:
    sys.stdout = old_stdout
    print(new_stdout.getvalue())
""".format(code.replace("\n", "\n    "))
        
        # Create a temporary file
        temp_filename = f"temp_exec_{int(time.time())}.py"
        headers = {"Content-Type": "application/json"}
        params = {"token": self.token}
        
        try:
            # Create the file with our code
            create_response = requests.put(
                f"{self.base_url}/api/contents/{temp_filename}",
                headers=headers,
                params=params,
                json={
                    "type": "file",
                    "format": "text",
                    "content": wrapped_code
                }
            )
            
            if create_response.status_code not in (200, 201):
                raise Exception(f"Failed to create temporary file: {create_response.status_code}")
            
            # Create a notebook to execute the file
            notebook_name = f"temp_runner_{int(time.time())}.ipynb"
            run_response = requests.post(
                f"{self.base_url}/api/contents",
                headers=headers,
                params=params,
                json={
                    "type": "notebook",
                    "path": notebook_name,
                    "format": "json",
                    "content": {
                        "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}},
                        "nbformat": 4,
                        "nbformat_minor": 5,
                        "cells": [
                            {
                                "cell_type": "code",
                                "execution_count": None,
                                "metadata": {},
                                "source": f"with open('{temp_filename}', 'r') as f:\n    exec(f.read())",
                                "outputs": []
                            }
                        ]
                    }
                }
            )
            
            if run_response.status_code != 201:
                raise Exception(f"Failed to create runner notebook: {run_response.status_code}")
                
            notebook_path = run_response.json().get("path", notebook_name)
            
            # Wait for execution
            time.sleep(3)
            
            # Get the notebook with results
            get_response = requests.get(
                f"{self.base_url}/api/contents/{notebook_path}",
                headers=headers,
                params=params
            )
            
            outputs = []
            if get_response.status_code == 200:
                notebook_data = get_response.json()
                cells = notebook_data.get("content", {}).get("cells", [])
                
                for cell in cells:
                    if cell.get("cell_type") == "code":
                        for cell_output in cell.get("outputs", []):
                            if "text" in cell_output:
                                outputs.append(cell_output["text"])
                            elif "data" in cell_output:
                                if "text/plain" in cell_output["data"]:
                                    outputs.append(cell_output["data"]["text/plain"])
            
            # Clean up
            try:
                requests.delete(f"{self.base_url}/api/contents/{temp_filename}", params=params)
                requests.delete(f"{self.base_url}/api/contents/{notebook_path}", params=params)
            except Exception as cleanup_error:
                self.logger.warning(f"Cleanup error: {str(cleanup_error)}")
            
            # Process the output
            result = "\n".join(outputs)
            
            # Extract results using our markers
            for line in result.split("\n"):
                if line.startswith("RESULT_MARKER:"):
                    result_part = line[len("RESULT_MARKER:"):].strip()
                if line.startswith("LATEX_MARKER:"):
                    latex_part = line[len("LATEX_MARKER:"):].strip()
                if line.startswith("ERROR_MARKER:"):
                    error_part = line[len("ERROR_MARKER:"):].strip()
                    return {"stdout": f"Error: {error_part}", "error": True}
            
            if result:
                # If we found marked results
                if 'result_part' in locals() and 'latex_part' in locals():
                    return {"stdout": f"RESULT: {result_part}\nLATEX: {latex_part}"}
                elif 'result_part' in locals():
                    return {"stdout": f"RESULT: {result_part}"}
                    
                # Otherwise return the raw output
                return {"stdout": result}
            else:
                return {"stdout": "# No output captured from temp file execution", "error": True}
                
        except Exception as e:
            self.logger.error(f"Error in temp file execution: {str(e)}")
            raise e
    
    def _check_kernel_alive(self):
        """Check if the kernel is still alive, recreate if needed"""
        try:
            headers = {"Content-Type": "application/json"}
            params = {}
            if self.token:
                params["token"] = self.token
                
            # Check kernel status
            response = requests.get(
                f"{self.base_url}/api/kernels/{self.kernel_id}",
                headers=headers,
                params=params,
                timeout=5
            )
            
            # If kernel not found, create a new one
            if response.status_code != 200:
                self.logger.warning(f"Kernel {self.kernel_id} not found (status: {response.status_code}). Creating new kernel.")
                self.kernel_id = None
                self._create_kernel()
                if not self.kernel_id:
                    raise RuntimeError("Failed to create a new kernel")
                    
        except Exception as e:
            self.logger.warning(f"Error checking kernel status: {str(e)}. Will try to create a new one.")
            self.kernel_id = None
            self._create_kernel()
            if not self.kernel_id:
                raise RuntimeError("Failed to create a new kernel")
    
    def compute_laplace_transform(self, expr):
        """
        Compute the Laplace transform of an expression using SageMath
        
        Args:
            expr (str): Mathematical expression in SageMath-compatible syntax
            
        Returns:
            str: LaTeX representation of the Laplace transform
        """
        # Fix common notations for unit step functions before sending to SageMath
        # Convert Heaviside to SageMath's heaviside
        expr = expr.replace('Heaviside', 'heaviside')
        
        # Handle unit step function notation - u_n(t) and subscript forms
        expr = re.sub(r'u_(\d+)\s*\(\s*([^)]+)\s*\)', r'heaviside(\2)', expr)
        
        # Fix unicode subscript notation for heaviside functions
        # Matches patterns like u₇(t-7)
        for i in range(10):
            expr = re.sub(f'u[₀₁₂₃₄₅₆₇₈₉]{{1}}\\s*\\(\\s*([^)]+)\\s*\\)', r'heaviside(\1)', expr)
        
        # Ensure proper handling of shifts in heaviside functions
        expr = re.sub(r'heaviside\s*\(\s*t\s*-\s*(\d+)\s*\)', r'heaviside(t-\1)', expr)
        
        # Make sure multiplication is explicit
        expr = re.sub(r'(\d+)t', r'\1*t', expr)
        expr = re.sub(r'(\d+)\(', r'\1*(', expr)
        expr = re.sub(r'([a-zA-Z0-9])\s+([a-zA-Z])', r'\1*\2', expr)
        
        # Prepare the SageMath code
        code = """
import re
var('t s')
f = {0}
try:
    result = laplace(f, t, s)
    print(f"RESULT: {{result}}")
    print(f"LATEX: {{latex(result)}}")
except Exception as e:
    print(f"ERROR: {{str(e)}}")
""".format(expr)
        
        try:
            result = self.execute(code)
            stdout = result.get("stdout", "")
            
            # Check for errors
            error_line = None
            for line in stdout.split("\n"):
                if line.startswith("ERROR:") or line.startswith("MANUAL ERROR:"):
                    error_line = line
            
            # Extract LaTeX result if available
            for line in stdout.split("\n"):
                if line.startswith("LATEX:"):
                    return line[7:].strip()
            
            # Fall back to RESULT if LATEX not found
            for line in stdout.split("\n"):
                if line.startswith("RESULT:"):
                    return line[8:].strip()
            
            # If we reached here, we couldn't find a proper result
            if error_line:
                raise ValueError(f"SageMath error: {error_line}")
            
            return stdout
        except Exception as e:
            self.logger.error(f"Error computing Laplace transform with SageMath: {str(e)}")
            raise ValueError(f"Failed to compute Laplace transform with SageMath: {str(e)}")
    
    def compute_fourier_series(self, expr, terms=5):
        """
        Compute the Fourier series of an expression using SageMath
        
        Args:
            expr (str): Mathematical expression in SageMath-compatible syntax
            terms (int): Number of terms to include in the series
            
        Returns:
            str: LaTeX representation of the Fourier series
        """
        # Make sure to define pi to avoid the "name 'pi' is not defined" error
        code = """
import numpy
from numpy import pi
from sympy import Symbol, pi as sympy_pi
var('x')
pi = numpy.pi  # Ensure pi is defined
f = {0}
try:
    result = fourier_series_partial_sum(f, x, pi, {1})
    print(f"RESULT: {{result}}")
    print(f"LATEX: {{latex(result)}}")
except Exception as e:
    print(f"ERROR: {{str(e)}}")
""".format(expr, terms)
        
        try:
            result = self.execute(code)
            stdout = result.get("stdout", "")
            
            # Check if the result contains the "No output captured" message
            if "# Direct evaluation executed:" in stdout and "# No output captured" in stdout:
                self.logger.warning(f"SageMath evaluation failed with no output captured")
                raise ValueError("SageMath computation failed with no output")
                
            # Check for explicit error messages
            for line in stdout.split("\n"):
                if line.startswith("ERROR:"):
                    raise ValueError(line[7:].strip())
            
            # Extract the LaTeX result if available
            for line in stdout.split("\n"):
                if line.startswith("LATEX:"):
                    return line[7:].strip()
            
            # Fall back to RESULT if LATEX not found
            for line in stdout.split("\n"):
                if line.startswith("RESULT:"):
                    return line[8:].strip()
                    
            # If we reach here and have output but no LATEX or RESULT markers,
            # the format might be unexpected but we should still return something
            if stdout.strip() and not "# No output captured" in stdout:
                return stdout.strip()
                
            # If we reach here, no usable output was found
            raise ValueError("Failed to parse SageMath output for Fourier series")
            
        except Exception as e:
            self.logger.error(f"Error computing Fourier series with SageMath: {str(e)}")
            raise ValueError(f"Failed to compute Fourier series with SageMath: {str(e)}")
            
    def solve_complex_equation(self, expr, is_system=False):
        """
        Solve a complex equation or system of equations using SageMath
        
        Args:
            expr (str): Mathematical expression in SageMath-compatible syntax
            is_system (bool): Whether this is a system of equations
            
        Returns:
            list: List of solutions in LaTeX format
        """
        if is_system:
            equations = [eq.strip() for eq in expr.split(",")]
            code = """
var('x y z')
system = [
"""
            for eq in equations:
                code += f"    {eq},\n"
            code += """
]
result = solve(system, [x, y, z])
print(f"RESULT: {result}")
for item in result:
    print(f"LATEX: {latex(item)}")
"""
        else:
            code = """
var('x y z')
try:
    eq = {0}
    result = solve(eq, x)
    print(f"RESULT: {{result}}")
    for item in result:
        print(f"LATEX: {{latex(item)}}")
except Exception as e:
    print(f"ERROR: {{str(e)}}")
""".format(expr)
        
        try:
            result = self.execute(code)
            stdout = result.get("stdout", "")
            
            # Check for error messages
            for line in stdout.split("\n"):
                if line.startswith("ERROR:"):
                    self.logger.error(f"SageMath error: {line}")
                    raise ValueError(line[7:].strip())
            
            # Check for empty result
            if "No output captured" in stdout or not stdout.strip():
                raise ValueError("SageMath returned no output")
            
            latex_results = []
            
            for line in stdout.split("\n"):
                if line.startswith("LATEX:"):
                    latex_results.append(line[7:].strip())
            
            if latex_results:
                return latex_results
            
            for line in stdout.split("\n"):
                if line.startswith("RESULT:"):
                    return [line[8:].strip()]
                    
            # If we reach here, we couldn't extract a proper result
            raise ValueError(f"Could not extract solution from SageMath output: {stdout}")
            
        except Exception as e:
            self.logger.error(f"Error solving equation with SageMath: {str(e)}")
            raise ValueError(f"Failed to solve equation with SageMath: {str(e)}")