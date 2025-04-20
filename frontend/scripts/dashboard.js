/**
 * Dashboard.js
 * Handles functionality for the user dashboard page
 */

// Initialize dashboard when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    initAuth();
    
    // Set up event listeners
    document.getElementById('logout-link').addEventListener('click', logout);
});

/**
 * Initialize authentication and check login status
 */
function initAuth() {
    // Check for saved auth token in localStorage
    const authToken = localStorage.getItem('authToken');
    const userJson = localStorage.getItem('currentUser');
    
    if (authToken && userJson) {
        try {
            const currentUser = JSON.parse(userJson);
            // Update UI
            document.getElementById('user-name').textContent = currentUser.username;
            
            // Set user initial in avatar
            const userInitial = document.getElementById('user-initial');
            if (userInitial && currentUser.username) {
                userInitial.textContent = currentUser.username.charAt(0).toUpperCase();
            }
            
            // Load user's saved calculations
            loadSavedCalculations(authToken);
        } catch (e) {
            console.error('Error parsing stored user data:', e);
            // Redirect to login page if there's an error
            window.location.href = '/login';
        }
    } else {
        // Not logged in, redirect to login page
        window.location.href = '/login';
    }
}

/**
 * Load the user's saved calculations
 */
async function loadSavedCalculations(authToken) {
    const calculationsList = document.getElementById('calculations-list');
    
    try {
        const response = await fetch('/api/calculations', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Render calculations
            renderSavedCalculations(data.calculations);
        } else {
            calculationsList.innerHTML = '<p>Error loading calculations. Please try again.</p>';
            console.error('Error loading calculations:', data.error);
        }
    } catch (error) {
        console.error('Error fetching calculations:', error);
        calculationsList.innerHTML = '<p>Error loading calculations. Please check your connection.</p>';
    }
}

/**
 * Render the user's saved calculations
 */
function renderSavedCalculations(calculations) {
    const calculationsList = document.getElementById('calculations-list');
    
    if (!calculations || calculations.length === 0) {
        calculationsList.innerHTML = '<p>You have no saved calculations yet. Go to the <a href="/">calculator</a> to solve and save calculations.</p>';
        return;
    }
    
    let html = '<div class="calculations-grid">';
    
    calculations.forEach(calc => {
        // Format date
        const date = new Date(calc.created_at);
        const formattedDate = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
        
        html += `
            <div class="calculation-card" data-id="${calc.id}">
                <div class="calculation-header">
                    <h3>${calc.title || `${calc.operation_type.toUpperCase()}`}</h3>
                    <span class="calculation-date">${formattedDate}</span>
                </div>
                <div class="calculation-input">
                    <strong>Input:</strong> \\(${calc.latex_input}\\)
                </div>
                <div class="calculation-solution">
                    <strong>Solution:</strong> \\(${calc.solution}\\)
                </div>
                <div class="calculation-actions">
                    <a href="/?calc=${calc.id}" class="btn btn-primary">Open in Calculator</a>
                    <button onclick="deleteSavedCalculation('${calc.id}')" class="btn btn-danger">Delete</button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    calculationsList.innerHTML = html;
    
    // Render LaTeX in the calculations list
    if (window.MathJax) {
        MathJax.typeset();
    }
}

/**
 * Delete a saved calculation
 */
async function deleteSavedCalculation(calculationId) {
    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
        return;
    }
    
    if (!confirm('Are you sure you want to delete this calculation?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/calculations/${calculationId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Refresh calculations list
            loadSavedCalculations(authToken);
        } else {
            alert('Error deleting calculation: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error deleting calculation:', error);
        alert('Error deleting calculation. Please try again.');
    }
}

/**
 * Handle user logout
 */
function logout(event) {
    if (event) {
        event.preventDefault();
    }
    
    // Clear auth state
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    // Redirect to login page
    window.location.href = '/login';
}