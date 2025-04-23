/**
 * User authentication and saved calculations functionality
 */

// Global variables for auth state
let isAuthenticated = false;
let currentUser = null;
let authToken = null;

/**
 * Initialize authentication from localStorage and cookies
 */
function initAuth() {
    // Check for saved auth token in localStorage and cookies
    authToken = localStorage.getItem('authToken') || getCookie('authToken');
    const userJson = localStorage.getItem('currentUser');
    
    if (authToken && userJson) {
        try {
            currentUser = JSON.parse(userJson);
            isAuthenticated = true;
            // Make authentication state available globally
            window.isAuthenticated = true;
            window.authToken = authToken;
            // Ensure the auth cookie is set (in case it was only in localStorage)
            setCookie('authToken', authToken, 7);
            updateAuthUI();
        } catch (e) {
            console.error('Error parsing stored user data:', e);
            logout(); // Clear invalid data
        }
    } else {
        window.isAuthenticated = false;
        window.authToken = null;
        updateAuthUI();
    }

    // Check current page and set up appropriate event listeners
    setupPageSpecificHandlers();
}

/**
 * Update the UI based on authentication state
 */
function updateAuthUI() {
    // Get UI elements that exist on all pages
    const userDisplay = document.getElementById('user-display');
    const logoutLink = document.getElementById('logout-link');
    const saveCalculationBtn = document.getElementById('save-calculation');
    
    if (userDisplay) {
        if (isAuthenticated && currentUser) {
            // User is logged in
            userDisplay.style.display = 'inline';
            
            // Update username display
            const usernameDisplay = document.getElementById('username-display');
            if (usernameDisplay) {
                usernameDisplay.textContent = currentUser.username || currentUser.email;
            }
            
            // Show save button if it exists and there's a solution
            if (saveCalculationBtn) {
                const solutionContainer = document.querySelector('.solution-container');
                if (solutionContainer && solutionContainer.textContent.trim()) {
                    saveCalculationBtn.style.display = 'inline-block';
                }
            }
        } else {
            // User is not logged in - they shouldn't be here, redirect to auth
            window.location.href = '/auth';
        }
    }
    
    // Setup logout handler
    if (logoutLink) {
        logoutLink.addEventListener('click', logout);
    }
}

/**
 * Set up page-specific event handlers based on current page
 */
function setupPageSpecificHandlers() {
    // Check if we're on the main calculator page
    const saveCalculationBtn = document.getElementById('save-calculation');
    if (saveCalculationBtn) {
        saveCalculationBtn.addEventListener('click', () => saveCurrentCalculation());
    }
    
    // If we're on the main page and there's a calculation ID in the URL, load it
    if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
        const urlParams = new URLSearchParams(window.location.search);
        const calcId = urlParams.get('calc');
        
        if (calcId && isAuthenticated) {
            // Load the calculation after a short delay to ensure page initialization
            setTimeout(() => loadSavedCalculation(calcId), 500);
        }
    }
}

/**
 * Get a cookie value by name
 */
function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for(let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

/**
 * Set a cookie
 */
function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

/**
 * Handle user logout
 */
function logout(event) {
    if (event) {
        event.preventDefault();
    }
    
    // Clear auth state
    isAuthenticated = false;
    currentUser = null;
    authToken = null;
    
    // Clear localStorage
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    // Clear cookie
    document.cookie = "authToken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    
    // Redirect to auth page
    window.location.href = '/auth';
}

/**
 * Load a saved calculation into the calculator
 */
async function loadSavedCalculation(calculationId) {
    if (!isAuthenticated || !authToken) {
        return;
    }
    
    try {
        const response = await fetch(`/api/calculations/${calculationId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const calc = data.calculation;
            
            // Set the input in the calculator
            if (window.currentMode === 'text') {
                document.getElementById('latex-input').value = calc.latex_input;
            } else {
                // If in drawing mode, switch to text mode first
                toggleMode('text');
                setTimeout(() => {
                    document.getElementById('latex-input').value = calc.latex_input;
                }, 300);
            }
            
            // Set the operation type
            const operationTypeSelect = document.getElementById('operation-type');
            if (operationTypeSelect) {
                operationTypeSelect.value = calc.operation_type;
            }
            
            // Calculate solution
            setTimeout(() => {
                // Trigger calculation (assuming this is a global function defined elsewhere)
                if (typeof calculateSolution === 'function') {
                    calculateSolution(calc.operation_type);
                } else if (typeof handleCalculate === 'function') {
                    handleCalculate();
                }
            }, 500);
        } else {
            console.error('Error loading calculation:', data.error);
        }
    } catch (error) {
        console.error('Error loading calculation:', error);
    }
}

/**
 * Save the current calculation
 * Can be called automatically after solving or manually via button
 */
async function saveCurrentCalculation(
  manualLatexInput = null, 
  manualSolution = null, 
  manualOperationType = null, 
  manualExplanation = null, 
  manualTitle = null
) {
    if (!isAuthenticated || !authToken) {
        alert('Please log in to save calculations');
        return;
    }
    
    // Get current calculation data - either from parameters or from DOM
    const latexInput = manualLatexInput || (window.currentMode === 'text' 
        ? document.getElementById('latex-input').value
        : document.getElementById('drawing-latex-result') 
          ? document.getElementById('drawing-latex-result').textContent
          : document.getElementById('result')?.dataset?.latex || '');
    
    const solutionContainer = document.querySelector('.solution-container');
    const solution = manualSolution || (solutionContainer ? solutionContainer.textContent.trim() : '');
    
    if (!latexInput || !solution) {
        if (!manualLatexInput && !manualSolution) {
            alert('No calculation to save');
        }
        return;
    }
    
    // Get operation type
    const operationTypeSelect = document.getElementById('operation-type');
    const operationType = manualOperationType || (operationTypeSelect ? operationTypeSelect.value : 'solve');
    
    // Get explanation if available
    const explanationContainer = document.querySelector('.explanation-container');
    const explanation = manualExplanation || (explanationContainer ? explanationContainer.textContent.trim() : '');
    
    // Optional title - use provided or prompt user
    let title = manualTitle;
    if (!title && !manualLatexInput) {  // Only prompt if not auto-saving
        title = prompt('Enter a title for this calculation (optional):');
    }
    
    try {
        const response = await fetch('/api/calculations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                latex_input: latexInput,
                operation_type: operationType,
                solution: solution,
                ai_explanation: explanation,
                title: title
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            if (!manualLatexInput) {  // Don't show alert if auto-saving
                alert('Calculation saved successfully! View it in My Calculations.');
            } else {
                console.log('Calculation auto-saved successfully');
                
                // Show save calculation button to indicate it was saved
                const saveCalculationBtn = document.getElementById('save-calculation');
                if (saveCalculationBtn) {
                    saveCalculationBtn.textContent = 'Saved!';
                    setTimeout(() => {
                        saveCalculationBtn.textContent = 'Save Calculation';
                    }, 2000);
                }
            }
        } else {
            console.error('Error saving calculation:', data.error || 'Unknown error');
            if (!manualLatexInput) {  // Don't show alert if auto-saving
                alert('Error saving calculation: ' + (data.error || 'Unknown error'));
            }
        }
    } catch (error) {
        console.error('Error saving calculation:', error);
        if (!manualLatexInput) {  // Don't show alert if auto-saving
            alert('Error saving calculation. Please try again.');
        }
    }
}

// Make saveCurrentCalculation globally available
window.saveCurrentCalculation = saveCurrentCalculation;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initAuth();
});