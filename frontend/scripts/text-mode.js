class TextMode {
  constructor(calculatorApp) {
    this.calculatorApp = calculatorApp;
  }
  
  init() {
    // Create placeholder UI for text mode
    this.createUI();
  }
  
  createUI() {
    // This is a placeholder for now - will be implemented later
    const template = `
      <div class="card">
        <div class="card-header">
          Type your math expression
        </div>
        <div class="placeholder-content" style="padding: 2rem; text-align: center;">
          <p>Text input mode will be implemented in a future update.</p>
        </div>
      </div>
    `;
    
    this.calculatorApp.mainContent.innerHTML = template;
  }
}