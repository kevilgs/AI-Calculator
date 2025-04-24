/**
 * Main Entry Point - Initializes the calculator application
 */

console.log("Checking MyScript iink library:", typeof iink !== 'undefined' ? "Loaded" : "Not loaded");

// Calculator class definition
class Calculator {
    constructor() {
        // Initialize properties
        this.editor = null;
        this.result = null;
        this.currentExpression = '';
        this.mainContent = document.getElementById('main-content');
        this.drawMode = null;
        this.textMode = null;
        this.currentMode = 'draw'; // Default mode
        
        // Bind methods to ensure 'this' context is preserved
        this.init = this.init.bind(this);
        this.switchMode = this.switchMode.bind(this);
        this.setupInstructionPopup = this.setupInstructionPopup.bind(this);
    }
    
    init() {
        // Initialize MyScript iink if using it
        this.initMyScript();
        
        // Initialize the default mode (draw mode)
        this.drawMode = new DrawMode(this);
        this.drawMode.init();
        
        // Initialize text mode (but don't show it)
        this.textMode = new TextMode(this);
        
        // Set up instruction popup
        this.setupInstructionPopup();
        
        // Set up event listeners for mode switching
        this.setupEventListeners();
    }
    
    initMyScript() {
        // Check if iink is loaded
        if (typeof window.iink === 'undefined') {
            console.error('MyScript iink library not loaded');
            return;
        }
        
        try {
            // Initialization is now handled in draw-mode.js
            console.log('MyScript iink library is loaded successfully');
        } catch (error) {
            console.error('Error initializing MyScript:', error);
        }
    }
    
    switchMode(mode) {
        if (mode === this.currentMode) return;
        
        // Update active button
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });
        
        // Switch the mode
        if (mode === 'draw') {
            this.drawMode.init();
        } else if (mode === 'text') {
            this.textMode.init();
        }
        
        this.currentMode = mode;
    }
    
    setupEventListeners() {
        // Set up mode switching
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.switchMode(btn.dataset.mode);
            });
        });
    }
    
    setupInstructionPopup() {
        // Get popup elements
        const popupOverlay = document.getElementById('instruction-popup-overlay');
        const closeButton = document.getElementById('close-instruction-popup');
        const infoButton = document.getElementById('info-button');
        
        // Set placeholder content for instructions
        document.getElementById('equation-instructions').innerHTML = 
            "Enter your equation here in standard mathematical notation. Example: 2x + 3 = 10 or x^2 + 3x + 64  = 1";
        document.getElementById('laplace-instructions').innerHTML = 
            "Enter your function for Laplace transform. No need to draw or type L Example: t^2 e^(-3t)";
        document.getElementById('fourier-instructions').innerHTML = 
            "Enter your function for Fourier series.  No need to draw or type f(x) and mention the limits in square prackets immediately for the main expression:Example: x^2[-π,π]";
        
        // Function to show popup
        const showPopup = () => {
            popupOverlay.classList.add('active');
        };
        
        // Function to hide popup
        const hidePopup = () => {
            popupOverlay.classList.remove('active');
            
            // Mark that the user has seen the popup
            localStorage.setItem('instructionPopupSeen', 'true');
        };
        
        // Add event listeners
        closeButton.addEventListener('click', hidePopup);
        infoButton.addEventListener('click', showPopup);
        
        // Close popup when clicking outside the popup content
        popupOverlay.addEventListener('click', (e) => {
            if (e.target === popupOverlay) {
                hidePopup();
            }
        });
        
        // Check if this is the first visit to the calculator page after login
        const checkFirstVisit = () => {
            const hasSeenPopup = localStorage.getItem('instructionPopupSeen') === 'true';
            const isLoggedIn = document.getElementById('username-display-nav').style.display !== 'none';
            const isCalculatorPage = window.location.pathname === '/' || window.location.pathname === '/index.html';
            
            // Show popup automatically on first visit after login
            if (isLoggedIn && isCalculatorPage && !hasSeenPopup) {
                showPopup();
            }
        };
        
        // Check after user authentication is verified
        const originalUpdateUIForLoggedInUser = window.updateUIForLoggedInUser;
        if (originalUpdateUIForLoggedInUser) {
            window.updateUIForLoggedInUser = function(username) {
                originalUpdateUIForLoggedInUser(username);
                
                // Wait a bit to ensure UI is updated
                setTimeout(checkFirstVisit, 500);
            };
        }
        
        // Also check on page load (in case user is already logged in)
        setTimeout(checkFirstVisit, 1000);
    }
}

// Create and initialize the calculator when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const calculator = new Calculator();
    calculator.init();
});