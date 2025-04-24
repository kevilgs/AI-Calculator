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
    
    // Set up sort functionality
    const sortSelect = document.getElementById('sort-calculations');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const authToken = localStorage.getItem('authToken');
            if (authToken) {
                loadSavedCalculations(authToken);
            }
        });
    }
    
    // Set up modal event listeners
    const modal = document.getElementById('pdf-modal');
    const closeModal = document.querySelector('.close-modal');
    const cancelPdf = document.getElementById('cancel-pdf');
    
    if (closeModal) {
        closeModal.addEventListener('click', function() {
            modal.classList.remove('show');
        });
    }
    
    if (cancelPdf) {
        cancelPdf.addEventListener('click', function() {
            modal.classList.remove('show');
        });
    }
    
    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.classList.remove('show');
        }
    });
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
            
            // Update navbar username
            const usernameDisplayNav = document.getElementById('username-display-nav');
            if (usernameDisplayNav) {
                usernameDisplayNav.style.display = 'inline';
                usernameDisplayNav.textContent = `Welcome, ${currentUser.username}`;
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
    const sortSelect = document.getElementById('sort-calculations');
    const sortValue = sortSelect ? sortSelect.value : 'date-desc';
    
    try {
        const response = await fetch('/api/calculations', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Sort calculations based on selected option
            const sortedCalculations = sortCalculations(data.calculations, sortValue);
            
            // Update total calculations stat
            updateStats(data.calculations.length);
            
            // Render calculations
            renderSavedCalculations(sortedCalculations);
        } else {
            calculationsList.innerHTML = '<p class="loading-text">Error loading calculations. Please try again.</p>';
            console.error('Error loading calculations:', data.error);
        }
    } catch (error) {
        console.error('Error fetching calculations:', error);
        calculationsList.innerHTML = '<p class="loading-text">Error loading calculations. Please check your connection.</p>';
    }
}

/**
 * Sort calculations based on selected option
 */
function sortCalculations(calculations, sortOption) {
    const sorted = [...calculations];
    
    switch (sortOption) {
        case 'date-desc':
            return sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        case 'date-asc':
            return sorted.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
        case 'type':
            return sorted.sort((a, b) => a.operation_type.localeCompare(b.operation_type));
        default:
            return sorted;
    }
}

/**
 * Update dashboard statistics
 */
function updateStats(totalCount) {
    const totalCalcElement = document.getElementById('total-calculations');
    if (totalCalcElement) {
        totalCalcElement.textContent = totalCount;
    }
}

/**
 * Render the user's saved calculations
 */
function renderSavedCalculations(calculations) {
    const calculationsList = document.getElementById('calculations-list');
    
    if (!calculations || calculations.length === 0) {
        calculationsList.innerHTML = '<p class="loading-text">You have no saved calculations yet. Go to the <a href="/index.html">calculator</a> to solve and save calculations.</p>';
        return;
    }
    
    let html = '<div class="calculations-grid">';
    
    calculations.forEach(calc => {
        // Format date
        const date = new Date(calc.created_at);
        const formattedDate = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
        
        // Create operation type badge based on type
        const operationType = calc.operation_type.charAt(0).toUpperCase() + calc.operation_type.slice(1);
        
        html += `
            <div class="calculation-card" data-id="${calc.id}">
                <div class="calculation-header">
                    <h3>${calc.title || `${operationType} Problem`}</h3>
                    <span class="calculation-date">${formattedDate}</span>
                </div>
                <div class="calculation-content">
                    <div class="calculation-input">
                        <strong>Input:</strong> \\(${calc.latex_input}\\)
                    </div>
                    <div class="calculation-solution">
                        <strong>Solution:</strong> \\(${calc.solution}\\)
                    </div>
                </div>
                <div class="calculation-actions">
                    <button onclick="convertToPDF('${calc.id}')" class="btn btn-primary">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"/>
                            <path d="M4.603 14.087a.81.81 0 0 1-.438-.42c-.195-.388-.13-.776.08-1.102.198-.307.526-.568.897-.787a7.68 7.68 0 0 1 1.482-.645 19.697 19.697 0 0 0 1.062-2.227a7.269 7.269 0 0 1-.43-1.295c-.086-.4-.119-.796-.046-1.136.075-.354.274-.672.65-.823.192-.077.4-.12.602-.077a.7.7 0 0 1 .477.365c.088.164.12.356.127.538.007.188-.012.396-.047.614-.084.51-.27 1.134-.52 1.794a10.954 10.954 0 0 0 .98 1.686 5.753 5.753 0 0 1 1.334.05c.364.066.734.195.96.465.12.144.193.32.2.518.007.192-.047.382-.138.563a1.04 1.04 0 0 1-.354.416.856.856 0 0 1-.51.138c-.331-.014-.654-.196-.933-.417a5.712 5.712 0 0 1-.911-.95a11.651 11.651 0 0 0-1.997.406 11.307 11.307 0 0 1-1.02 1.51c-.292.35-.609.656-.927.787a.793.793 0 0 1-.58.029z"/>
                        </svg>
                        Convert to PDF
                    </button>
                    <button onclick="deleteSavedCalculation('${calc.id}')" class="btn-icon delete-btn">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                            <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                        </svg>
                    </button>
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
 * Convert calculation to PDF
 */
function convertToPDF(calculationId) {
    const authToken = localStorage.getItem('authToken');
    if (!authToken) return;
    
    // Show the modal with a preview first
    const pdfPreview = document.getElementById('pdf-preview');
    pdfPreview.innerHTML = '<div class="loading-text">Loading calculation details...</div>';
    
    // Show the modal
    const modal = document.getElementById('pdf-modal');
    modal.classList.add('show');
    
    try {
        // Fetch the complete calculation details from the API
        fetch(`/api/calculations/${calculationId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Could not fetch calculation details');
            }
            return response.json();
        })
        .then(data => {
            if (!data.success || !data.calculation) {
                throw new Error('Invalid calculation data received');
            }
            
            const calc = data.calculation;
            
            // Format date
            const date = new Date(calc.created_at);
            const formattedDate = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
            
            // Create operation type label
            const operationType = calc.operation_type.charAt(0).toUpperCase() + calc.operation_type.slice(1);
            
            // Process the AI explanation to handle markdown syntax
            let processedExplanation = '';
            if (calc.ai_explanation) {
                // Replace ** with <strong> tags for bold text
                processedExplanation = calc.ai_explanation
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    // Replace * with <em> tags for italic text
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    // Handle line breaks
                    .replace(/\n/g, '<br>');
            }
            
            // Create PDF preview content
            pdfPreview.innerHTML = `
                <div class="pdf-content">
                    <div class="pdf-header">
                        <h2>${calc.title || `${operationType} Problem`}</h2>
                        <p class="pdf-date">${formattedDate}</p>
                    </div>
                    
                    <div class="pdf-section">
                        <h3>Problem</h3>
                        <div class="pdf-math-content">
                            <div class="latex-content">\\(${calc.latex_input}\\)</div>
                        </div>
                    </div>
                    
                    <div class="pdf-section">
                        <h3>Solution</h3>
                        <div class="pdf-math-content">
                            <div class="latex-content">\\(${calc.solution}\\)</div>
                        </div>
                    </div>
                    
                    ${calc.ai_explanation ? `
                    <div class="pdf-section">
                        <h3>Explanation</h3>
                        <div class="pdf-explanation">${processedExplanation}</div>
                    </div>
                    ` : ''}
                    
                    <div class="pdf-footer">
                        <p>Generated by MathSolver AI</p>
                    </div>
                </div>
                <div class="pdf-info">
                    <p>Click "Download PDF" to generate a high-quality PDF file with proper formatting.</p>
                </div>
            `;
            
            // Add styling to the PDF preview content
            const style = document.createElement('style');
            style.textContent = `
                .pdf-content {
                    font-family: 'Poppins', Arial, sans-serif;
                    color: #37374a;
                    max-width: 100%;
                    padding: 20px;
                    background-color: white;
                    border-radius: 8px;
                    border: 1px solid #e0e0f5;
                }
                .pdf-header {
                    text-align: center;
                    margin-bottom: 25px;
                    padding-bottom: 15px;
                    border-bottom: 2px solid #e0e0f5;
                }
                .pdf-header h2 {
                    color: #6200ea;
                    margin-bottom: 5px;
                    font-size: 24px;
                }
                .pdf-date {
                    color: #6b6b80;
                    font-size: 12px;
                    margin: 0;
                }
                .pdf-section {
                    margin-bottom: 25px;
                    padding: 15px;
                    background-color: #f8f9ff;
                    border-radius: 8px;
                    border: 1px solid #e0e0f5;
                }
                .pdf-section h3 {
                    margin-top: 0;
                    margin-bottom: 15px;
                    color: #6200ea;
                    font-size: 18px;
                    font-weight: 600;
                }
                .pdf-math-content {
                    display: flex;
                    justify-content: center;
                    margin: 15px 0;
                    font-size: 18px;
                }
                .pdf-explanation {
                    line-height: 1.6;
                    white-space: normal;
                    font-size: 14px;
                    padding: 0 10px;
                }
                .pdf-explanation strong {
                    font-weight: bold;
                }
                .pdf-explanation em {
                    font-style: italic;
                }
                .pdf-footer {
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 15px;
                    border-top: 1px solid #e0e0f5;
                    font-size: 12px;
                    color: #6b6b80;
                }
                .pdf-info {
                    margin-top: 20px;
                    padding: 10px;
                    background-color: #f0f8ff;
                    border-radius: 8px;
                    border: 1px solid #d0e0ff;
                    text-align: center;
                    color: #4a5568;
                }
            `;
            pdfPreview.appendChild(style);
            
            // Render LaTeX in the preview
            if (window.MathJax) {
                MathJax.typeset();
            }
            
            // Set up download button
            const downloadButton = document.getElementById('download-pdf');
            downloadButton.onclick = function() {
                downloadServerGeneratedPDF(calculationId, calc.title || `${operationType} Problem`);
            };
        })
        .catch(error => {
            console.error('Error preparing PDF:', error);
            pdfPreview.innerHTML = `<div class="error-message">
                <p>Error loading calculation details. Please try again.</p>
                <p>${error.message}</p>
            </div>`;
        });
    } catch (error) {
        console.error('Error preparing PDF:', error);
        pdfPreview.innerHTML = `<div class="error-message">
            <p>Error loading calculation details. Please try again.</p>
            <p>${error.message}</p>
        </div>`;
    }
}

/**
 * Download a server-generated PDF for a calculation
 */
function downloadServerGeneratedPDF(calculationId, title) {
    const authToken = localStorage.getItem('authToken');
    if (!authToken) return;
    
    // Show loading state
    const downloadButton = document.getElementById('download-pdf');
    const originalText = downloadButton.textContent;
    downloadButton.textContent = 'Generating PDF...';
    downloadButton.disabled = true;
    
    // Generate the PDF on the server and download it
    const pdfUrl = `/api/calculations/${calculationId}/pdf`;
    
    // Create a hidden anchor to trigger the download
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = pdfUrl;
    a.setAttribute('download', title.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.pdf');
    
    // Add the auth token to the link
    a.setAttribute('data-auth', `Bearer ${authToken}`);
    
    // We need to create a fetch request with the auth token and then create a blob URL
    fetch(pdfUrl, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to generate PDF');
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        a.href = url;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        
        // Update button state
        downloadButton.textContent = 'PDF Downloaded!';
        setTimeout(() => {
            downloadButton.textContent = originalText;
            downloadButton.disabled = false;
        }, 2000);
    })
    .catch(error => {
        console.error('Error downloading PDF:', error);
        downloadButton.textContent = 'Error, try again';
        downloadButton.disabled = false;
        setTimeout(() => {
            downloadButton.textContent = originalText;
            downloadButton.disabled = false;
        }, 2000);
    });
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
            // Find and remove the calculation card with animation
            const card = document.querySelector(`.calculation-card[data-id="${calculationId}"]`);
            if (card) {
                card.style.transition = 'all 0.3s ease-out';
                card.style.transform = 'translateX(30px)';
                card.style.opacity = '0';
                
                setTimeout(() => {
                    // Refresh calculations list after animation
                    loadSavedCalculations(authToken);
                }, 300);
            } else {
                // Fallback if card not found
                loadSavedCalculations(authToken);
            }
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
    
    // Clear cookie if it exists
    document.cookie = "authToken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    
    // Redirect to login page
    window.location.href = '/login';
}