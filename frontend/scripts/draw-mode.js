class DrawMode {
  constructor(calculator) {
    this.calculator = calculator;
    // Set up options
    this.options = {
      configuration: {
        recognition: {
          type: "MATH",
          math: {
            mimeTypes: ["application/x-latex"],
            eraser: {
              "erase-precisely": false
            }
          }
        },
        server: {
          applicationKey: "468ee285-66e1-4c82-9bfa-01fa9159e4c3",
          hmacKey: "cd7e32be-8dcd-4d45-a5bd-02741d6f77ed"
        }
      }
    };
  }
  
  init() {
    // Create the UI elements
    this.createUI();
    
    // Initialize the editor
    this.loadEditor().then(() => {
      this.setupEventListeners();
    });
  }
  
  createUI() {
    // Create the UI elements for the math editor
    const template = `
      <div class="toolbar">
        <div class="tools">
          <button id="undo" class="tool-btn" disabled>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7v6h6"></path><path d="M21 17a9 9 0 00-9-9 9 9 0 00-6 2.3L3 13"></path></svg>
          </button>
          <button id="redo" class="tool-btn" disabled>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 7v6h-6"></path><path d="M3 17a9 9 0 019-9 9 9 0 016 2.3L21 13"></path></svg>
          </button>
          <button id="clear" class="tool-btn" disabled>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"></path></svg>
          </button>
        </div>
        <div class="tools">
          <button id="pen" class="tool-btn active" disabled>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19l7-7 3 3-7 7-3-3z"></path><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"></path><path d="M2 2l7.586 7.586"></path><circle cx="11" cy="11" r="2"></circle></svg>
          </button>
          <button id="eraser" class="tool-btn">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 20H7L3 16c-.8-.8-.8-2 0-2.8L13.8 2.4c.8-.8 2-.8 2.8 0L20 6"></path><path d="M6 14l8 8h8"></path></svg>
          </button>
        </div>
        <div class="options">
          <label class="option-label">
            <span>Precise Erase</span>
            <label class="switch">
              <input type="checkbox" id="erase-precisely">
              <span class="slider"></span>
            </label>
          </label>
        </div>
      </div>
      <div id="editor" class="drawing-area"></div>
      <div class="result-card">
        <div id="result">Your expression will appear here</div>
      </div>
    `;
    
    // Add the template to the main content
    this.calculator.mainContent.innerHTML = template;
    
    // Add a solve button to the result card
    const resultCard = document.querySelector('.result-card');
    if (resultCard) {
      const solveButton = document.createElement('button');
      solveButton.id = 'solve-btn';
      solveButton.className = 'solve-btn';
      solveButton.textContent = 'Solve';
      solveButton.disabled = true; // Initially disabled until there's an expression
      resultCard.appendChild(solveButton);
    }
  }
  
  async loadEditor() {
    try {
      const editorElement = document.getElementById("editor");
      
      // Check if the iink object exists in window
      if (typeof window.iink === 'undefined') {
        console.error("iink library not found. Make sure it's properly loaded.");
        const resultElement = document.getElementById("result");
        resultElement.innerHTML = "Error: MyScript iink library not loaded. Please check the console for details.";
        return;
      }
      
      // Initialize the editor correctly using iink.Editor.load as per documentation
      // First check if we have server configuration
      if (!this.options.configuration.server) {
        console.error("Server configuration is missing");
        return;
      }
      
      // Initialize the editor with the correct method
      this.editor = await iink.Editor.load(editorElement, "INTERACTIVEINKSSR", this.options);
      console.log("Editor initialized successfully");
      
    } catch (error) {
      console.error("Error loading the editor:", error);
      const resultElement = document.getElementById("result");
      resultElement.innerHTML = `Failed to load the drawing editor: ${error.message}`;
    }
  }
  
  setupEventListeners() {
    // Wait for editor to be loaded before setting up event listeners
    const checkEditor = setInterval(() => {
      if (this.editor) {
        clearInterval(checkEditor);
        
        const editorElement = document.getElementById("editor");
        const resultElement = document.getElementById("result");
        const undoElement = document.getElementById("undo");
        const redoElement = document.getElementById("redo");
        const clearElement = document.getElementById("clear");
        const eraserElement = document.getElementById("eraser");
        const penElement = document.getElementById("pen");
        const erasePreciselyElement = document.getElementById("erase-precisely");
        
        // Editor change events
        editorElement.addEventListener("changed", (event) => {
          undoElement.disabled = !event.detail.canUndo;
          redoElement.disabled = !event.detail.canRedo;
          clearElement.disabled = event.detail.isEmpty;
        });
        
        // Export events
        editorElement.addEventListener("exported", (evt) => {
          const exports = evt.detail;
          if (exports && exports["application/x-latex"]) {
            try {
              const latexContent = this.cleanLatex(exports["application/x-latex"]);
              
              // Store the raw LaTeX for later use
              resultElement.dataset.latex = latexContent;
              
              // Render with KaTeX
              katex.render(latexContent, resultElement);
              
            } catch (error) {
              resultElement.innerHTML = '<span>' + this.cleanLatex(exports['application/x-latex']) + '</span>';
              console.error("Error rendering LaTeX:", error);
            }
          } else {
            resultElement.innerHTML = "Your expression will appear here";
          }
        });
        
        // Button events
        undoElement.addEventListener("click", () => {
          this.editor.undo();
        });
        
        redoElement.addEventListener("click", () => {
          this.editor.redo();
        });
        
        clearElement.addEventListener("click", () => {
          this.editor.clear();
        });
        
        eraserElement.addEventListener("click", () => {
          this.editor.tool = iink.EditorTool.Erase;
          eraserElement.disabled = true;
          eraserElement.classList.add("active");
          penElement.disabled = false;
          penElement.classList.remove("active");
        });
        
        penElement.addEventListener("click", () => {
          this.editor.tool = iink.EditorTool.Write;
          eraserElement.disabled = false;
          eraserElement.classList.remove("active");
          penElement.disabled = true;
          penElement.classList.add("active");
        });
        
        erasePreciselyElement.addEventListener("change", (e) => {
          this.options.configuration.recognition.math.eraser["erase-precisely"] = e.target.checked;
          // Reinitialize editor with new settings
          this.loadEditor().then(() => {
            eraserElement.disabled = false;
            eraserElement.classList.remove("active");
            penElement.disabled = true;
            penElement.classList.add("active");
          });
        });
        
        // Handle window resize
        window.addEventListener("resize", () => {
          this.editor.resize();
        });
        
        // Add the solve button functionality
        const solveButton = document.getElementById('solve-btn');
        if (solveButton && resultElement) {
          // Enable solve button when there's a valid expression
          editorElement.addEventListener("exported", () => {
            const hasExpression = resultElement.dataset.latex && 
                                 resultElement.dataset.latex.trim() !== '';
            solveButton.disabled = !hasExpression;
          });
          
          // Handle solve button click
          solveButton.addEventListener('click', async () => {
            const latex = resultElement.dataset.latex;
            if (!latex) return;
            
            // Show loading state
            solveButton.disabled = true;
            solveButton.textContent = 'Solving...';
            
            try {
              // Get the selected operation type from the topic select dropdown
              const topicSelect = document.getElementById('topic');
              let operationType = 'solve';
              
              if (topicSelect) {
                // Use the selected topic if available
                operationType = topicSelect.value;
              } else {
                // Fallback to automatic detection based on content
                if (latex.includes('\\mathcal{L}') || latex.includes('laplace')) {
                  operationType = 'laplace';
                } else if (latex.includes('\\sum') || latex.includes('fourier')) {
                  operationType = 'fourier';
                } else if (latex.includes('\\sin') || latex.includes('\\cos') || 
                           latex.includes('sin') || latex.includes('cos') || 
                           latex.includes('t)')) {
                  // If the expression contains trigonometric functions or t variable, 
                  // it's likely to be a Laplace transform candidate
                  operationType = 'laplace';
                }
              }
              
              console.log(`Using operation type: ${operationType} for expression: ${latex}`);
              
              // Send to backend
              const response = await fetch('http://localhost:5000/api/solve', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                  latex: latex,
                  operation_type: operationType
                })
              });
              
              if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
              }
              
              const data = await response.json();
              
              // Create solution display
              this.displaySolution(data);
            } catch (error) {
              console.error('Error solving expression:', error);
              this.displayError(`Error: ${error.message}`);
            } finally {
              // Reset button state
              solveButton.disabled = false;
              solveButton.textContent = 'Solve';
            }
          });
        }
      }
    }, 100);
  }
  
  cleanLatex(latexExport) {
    if (latexExport.includes("\\\\")) {
      const steps = "\\begin{align*}" + latexExport + "\\end{align*}";
      return steps.replace("\\begin{aligned}", "").replace("\\end{aligned}", "").replace(new RegExp("(align.{1})", "g"), "aligned");
    }
    return latexExport.replace(new RegExp("(align.{1})", "g"), "aligned");
  }
  
  displaySolution(solution) {
    // Log the solution data to debug
    console.log("Solution data received:", solution);
    
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
        
        // Create a LaTeX format for multiple solutions - typically x = ... or ...
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