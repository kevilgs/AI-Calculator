class TextMode {
  constructor(calculatorApp) {
    this.calculatorApp = calculatorApp;
    this.currentLatex = '';
  }
  
  init() {
    // Create UI for text mode
    this.createUI();
    
    // Set up event listeners after UI is created
    this.setupEventListeners();
  }
  
  createUI() {
    const template = `
      <div class="card text-mode-card">
        <div class="card-header">
          <h3>Type your math expression</h3>
        </div>
        <div class="card-body">
          <div class="input-wrapper">
            <textarea id="text-input" class="math-text-input" placeholder="Type your mathematical expression here..."></textarea>
          </div>
          <div class="preview-wrapper">
            <div class="preview-header">Preview:</div>
            <div id="text-preview" class="math-preview">Your expression will appear here</div>
          </div>
          <div class="button-wrapper">
            <button id="text-solve-btn" class="solve-btn" disabled>Solve</button>
          </div>
        </div>
        <div class="card-footer">
          <div class="typing-hints">
            <h4>Typing Hints:</h4>
            <ul>
              <li>Use ^ for exponents: x^2</li>
              <li>Use / for fractions: 1/3</li>
              <li>Greek letters: \\alpha, \\beta, \\pi</li>
              <li>Functions: \\sin, \\cos, \\tan, \\sqrt</li>
              <li>For subscripts use _: a_1</li>
            </ul>
          </div>
        </div>
      </div>
    `;
    
    // Update the main content
    this.calculatorApp.mainContent.innerHTML = template;
    
    // Update placeholder based on currently selected operation type
    this.updatePlaceholderBasedOnOperation();
  }
  
  updatePlaceholderBasedOnOperation() {
    const textInput = document.getElementById('text-input');
    const operationTypeSelect = document.getElementById('operation-type');
    
    if (!textInput || !operationTypeSelect) return;
    
    // Update placeholder based on selected operation
    switch (operationTypeSelect.value) {
      case 'laplace':
        textInput.placeholder = 'Enter expression for Laplace transform (e.g., t^2*e^(-3t))';
        break;
      case 'fourier':
        textInput.placeholder = 'Enter expression for Fourier series (e.g., x^2) with domain [a,b]';
        break;
      default: // solve
        textInput.placeholder = 'Enter equation to solve (e.g., x^2 + 3x + 2 = 0)';
    }
  }
  
  setupEventListeners() {
    const textInput = document.getElementById('text-input');
    const previewElement = document.getElementById('text-preview');
    const solveButton = document.getElementById('text-solve-btn');
    const operationTypeSelect = document.getElementById('operation-type');
    
    if (!textInput || !previewElement || !solveButton || !operationTypeSelect) {
      console.error('Required text mode elements not found');
      return;
    }
    
    // Listen for input to update the preview
    textInput.addEventListener('input', (e) => {
      const inputValue = e.target.value;
      this.renderPreview(inputValue);
      
      // Enable/disable solve button based on input
      solveButton.disabled = !inputValue.trim();
    });
    
    // Listen for changes in the global operation type selector
    operationTypeSelect.addEventListener('change', () => {
      // Update the placeholder text
      this.updatePlaceholderBasedOnOperation();
      
      // Re-render preview with any existing input
      if (textInput.value.trim()) {
        this.renderPreview(textInput.value);
      }
    });
    
    // Handle solve button click
    solveButton.addEventListener('click', () => {
      this.solveExpression();
    });
    
    // Also trigger solve on Enter key if Ctrl is pressed
    textInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        if (!solveButton.disabled) {
          this.solveExpression();
        }
      }
    });
  }
  
  renderPreview(inputText) {
    const previewElement = document.getElementById('text-preview');
    
    if (!inputText.trim()) {
      previewElement.innerHTML = 'Your expression will appear here';
      this.currentLatex = '';
      return;
    }
    
    // Store the processed LaTeX
    this.currentLatex = this.processInputToLatex(inputText);
    
    // Render with KaTeX
    try {
      katex.render(this.currentLatex, previewElement);
      previewElement.dataset.latex = this.currentLatex;
    } catch (error) {
      console.error('Error rendering LaTeX in text mode:', error);
      previewElement.innerHTML = '<span class="error">Error rendering expression</span>';
    }
  }
  
  processInputToLatex(input) {
    // Get the current operation type
    const operationTypeSelect = document.getElementById('operation-type');
    const operationType = operationTypeSelect ? operationTypeSelect.value : 'solve';
    
    // Basic processing - convert plain text input to proper LaTeX
    let latex = input;
    
    // Remove explicit * multiplication symbols (making them implicit in LaTeX)
    // But be careful not to remove * from other contexts like function names
    latex = latex.replace(/([0-9a-zA-Z\)}])(\s*)\*(\s*)([0-9a-zA-Z\({])/g, '$1$2$3$4');
    
    // Handle implied multiplication (juxtaposition)
    // This helps when users type things like t^2e^(-3t) without *
    latex = latex.replace(/([0-9])([a-zA-Z])/g, '$1 $2'); // Add space between number and variable
    
    // Fix for expressions like t^2e^(-3t) - add invisible multiplication
    // Look for variable followed by function-like term
    latex = latex.replace(/([a-zA-Z0-9\}])([a-zA-Z]+\^)/g, '$1 $2');
    
    // Fix exponents with parentheses - e.g., e^(-3t) to e^{-3t}
    // This regex matches patterns like ^(expression) and replaces with ^{expression}
    latex = latex.replace(/\^(-?\(.*?\)|\([^)]*\))/g, function(match) {
      // Extract the content inside parentheses
      const exponent = match.substring(2, match.length - 1);
      // Return with curly braces for proper LaTeX rendering
      return `^{${exponent}}`;
    });
    
    // Also handle simple negative exponents without parentheses - e.g., e^-3t to e^{-3t}
    latex = latex.replace(/\^-([a-zA-Z0-9]+)/g, '^{-$1}');
    
    // Handle regular exponents - without proper curly braces - e.g., t^2 to t^{2}
    latex = latex.replace(/\^([a-zA-Z0-9]+)/g, '^{$1}');
    
    // If this is for Fourier series, handle domain specification
    if (operationType === 'fourier') {
      // Check for domain specification like x^2[-π,π]
      const domainMatch = latex.match(/(.*)\[(.*),(.*)\]$/);
      if (domainMatch) {
        // Extract expression and domain
        const expr = domainMatch[1];
        const lowerBound = domainMatch[2];
        const upperBound = domainMatch[3];
        
        // Format with proper domain notation
        latex = `${expr} \\text{ on } [${lowerBound},${upperBound}]`;
      }
    }
    
    return latex;
  }
  
  async solveExpression() {
    // Get the input and operation type from the global selector
    const inputElement = document.getElementById('text-input');
    const solveButton = document.getElementById('text-solve-btn');
    const operationTypeSelect = document.getElementById('operation-type');
    
    if (!inputElement || !this.currentLatex || !operationTypeSelect) {
      console.error('Missing input for solving');
      return;
    }
    
    const operationType = operationTypeSelect.value;
    
    // Show loading state
    solveButton.disabled = true;
    solveButton.textContent = 'Solving...';
    
    try {
      console.log(`Using operation type: ${operationType} for expression: ${this.currentLatex}`);
      
      // Send to backend
      const response = await fetch('http://localhost:5000/api/solve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          latex: this.currentLatex,
          operation_type: operationType
        })
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Display the solution
      this.displaySolution(data);
    } catch (error) {
      console.error('Error solving expression:', error);
      this.displayError(`Error: ${error.message}`);
    } finally {
      // Reset button state
      solveButton.disabled = false;
      solveButton.textContent = 'Solve';
    }
  }
  
  displaySolution(solution) {
    // Create solution container
    let solutionContainer = document.querySelector('.solution-container');
    if (!solutionContainer) {
      solutionContainer = document.createElement('div');
      solutionContainer.className = 'solution-container';
      document.getElementById('main-content').appendChild(solutionContainer);
    } else {
      // Clear existing content
      solutionContainer.innerHTML = '';
    }
    
    // Make sure the solution container is visible
    solutionContainer.style.display = 'block';
    
    // Create header
    const header = document.createElement('div');
    header.className = 'solution-header';
    header.textContent = 'Solution';
    solutionContainer.appendChild(header);
    
    // Create result
    const result = document.createElement('div');
    result.className = 'solution-result';
    
    if (solution.error) {
      result.innerHTML = `<div class="error">${solution.error}</div>`;
    } else {
      // For equations that have multiple solutions, display all of them
      if (Array.isArray(solution.solution) && solution.solution.length > 1) {
        // Create a container for multiple solutions
        let solutionsHtml = '';
        
        // Create a LaTeX format for multiple solutions
        if (solution.solution.every(sol => sol.includes('='))) {
          // Solutions already have equals sign
          solutionsHtml = solution.solution.join(', \\; ');
        } else {
          // Solutions don't have equals sign, add x = for clarity
          solutionsHtml = 'x = ' + solution.solution.join(', \\; x = ');
        }
        
        // Render with KaTeX
        try {
          katex.render(solutionsHtml, result);
        } catch (e) {
          console.error("Error rendering multiple solutions with KaTeX:", e);
          result.innerHTML = `<div>${solutionsHtml}</div>`;
        }
      } else {
        // Single solution or other type of result
        const solutionText = Array.isArray(solution.solution) ? solution.solution[0] : solution.solution;
        
        // Render with KaTeX
        try {
          katex.render(solutionText, result);
        } catch (e) {
          console.error("Error rendering solution with KaTeX:", e);
          result.textContent = solutionText;
        }
      }
    }
    
    solutionContainer.appendChild(result);
    
    // Create steps section for AI steps
    if (solution.ai_steps && solution.ai_steps.length > 0) {
      const stepsContainer = document.createElement('div');
      stepsContainer.className = 'solution-steps';
      stepsContainer.innerHTML = '<div class="steps-header">Steps:</div>';
      
      const stepsContent = document.createElement('div');
      stepsContent.className = 'steps-content';
      
      // Process each step to convert LaTeX expressions
      solution.ai_steps.forEach((step, index) => {
        // Create element for this step
        const stepElement = document.createElement('div');
        stepElement.className = 'step';
        
        // Process Markdown-style formatting
        let processedStep = step
          // Convert **text** to <strong>text</strong> (bold)
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          // Convert *text* to <em>text</em> (italics)
          .replace(/\*(.*?)\*/g, '<em>$1</em>');
          
        // Handle inline LaTeX - wrap $..$ in katex render spans
        processedStep = processedStep.replace(/\$(.*?)\$/g, (match, p1) => {
          // Create a unique ID for this math element
          const mathId = 'math-' + index + '-' + Math.random().toString(36).substr(2, 9);
          // Return a span with the ID that will be rendered later
          return `<span id="${mathId}" class="math-inline">${p1}</span>`;
        });
        
        // Handle numbered lists 
        if (/^\d+\./.test(processedStep)) {
          // This is a numbered list item
          processedStep = processedStep.replace(/^(\d+\.)\s(.*)/, '<li>$2</li>');
          
          // If we're not already in a list, start one
          if (!stepsContent.innerHTML.endsWith('</ol>') && !stepsContent.innerHTML.endsWith('<ol>')) {
            stepElement.innerHTML = '<ol>' + processedStep;
          } else {
            stepElement.innerHTML = processedStep;
          }
          
          // If this is the last step or the next step doesn't have a list item, close the list
          if (index === solution.ai_steps.length - 1 || 
              !solution.ai_steps[index + 1].match(/^\d+\.\s/)) {
            stepElement.innerHTML += '</ol>';
          }
        } else {
          // Regular paragraph
          stepElement.innerHTML = `<p>${processedStep}</p>`;
        }
        
        stepsContent.appendChild(stepElement);
      });
      
      stepsContainer.appendChild(stepsContent);
      solutionContainer.appendChild(stepsContainer);
      
      // Render all LaTeX math expressions after the DOM is updated
      setTimeout(() => {
        document.querySelectorAll('.math-inline').forEach(mathElement => {
          try {
            katex.render(mathElement.textContent, mathElement, {
              displayMode: false,
              throwOnError: false
            });
          } catch (e) {
            console.error("Failed to render math:", e);
          }
        });
      }, 0);
    }
    
    // Scroll to the solution
    solutionContainer.scrollIntoView({behavior: 'smooth'});
    
    // Auto-save the calculation if the user is authenticated
    if (window.isAuthenticated && typeof window.saveCurrentCalculation === 'function' && !solution.error) {
      // Auto-save with a brief delay to ensure UI is updated first
      setTimeout(() => {
        console.log("Auto-saving calculation...");
        this.autoSaveCalculation(solution);
      }, 1000);
    }
  }
  
  autoSaveCalculation(solution) {
    // Get the current input
    const inputElement = document.getElementById("text-input");
    const latexInput = this.currentLatex;
    const operationTypeSelect = document.getElementById('operation-type');
    const operationType = operationTypeSelect ? operationTypeSelect.value : 'solve';
    
    if (!latexInput || !solution.solution) {
      console.error("Missing required data for auto-save", {
        latexInput: latexInput ? "exists" : "missing",
        solution: solution.solution ? "exists" : "missing"
      });
      return;
    }
    
    // Format the solution text
    const solutionText = Array.isArray(solution.solution) ? solution.solution.join(', ') : solution.solution;
    
    // Get explanation if available
    const explanation = solution.ai_steps ? solution.ai_steps.join('\n') : '';
    
    // Generate a title based on operation type and date
    const title = `${operationType.charAt(0).toUpperCase() + operationType.slice(1)} - ${new Date().toLocaleString()}`;
    
    // Call the save function if it exists
    if (typeof window.saveCurrentCalculation === 'function') {
      window.saveCurrentCalculation(
        latexInput,
        solutionText,
        operationType,
        explanation,
        title
      );
    } else {
      console.error("saveCurrentCalculation function not available globally");
    }
  }
  
  displayError(errorMessage) {
    // Create solution container if it doesn't exist
    let solutionContainer = document.querySelector('.solution-container');
    if (!solutionContainer) {
      solutionContainer = document.createElement('div');
      solutionContainer.className = 'solution-container';
      document.getElementById('main-content').appendChild(solutionContainer);
    } else {
      // Clear existing content
      solutionContainer.innerHTML = '';
    }
    
    // Create header
    const header = document.createElement('div');
    header.className = 'solution-header';
    header.textContent = 'Error';
    solutionContainer.appendChild(header);
    
    // Create error message
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.textContent = errorMessage;
    solutionContainer.appendChild(errorElement);
  }
}