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
    }
    
    init() {
        // Initialize MyScript iink if using it
        this.initMyScript();
        
        // Initialize the default mode (draw mode)
        this.drawMode = new DrawMode(this);
        this.drawMode.init();
        
        // Initialize text mode (but don't show it)
        this.textMode = new TextMode(this);
        
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
}

// Create and initialize the calculator when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const calculator = new Calculator();
    calculator.init();
});