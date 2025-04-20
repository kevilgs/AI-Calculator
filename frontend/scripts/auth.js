document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('authForm');
  const toggleBtns = document.querySelectorAll('.toggle-btn');
  const nameGroup = document.querySelector('.name-group');
  const emailGroup = document.querySelector('.email-group');
  const usernameGroup = document.querySelector('.username-group');
  const passwordHint = document.querySelector('.password-hint');
  const togglePasswordBtn = document.querySelector('.toggle-password');
  const submitBtn = document.querySelector('.submit-btn');
  let isLogin = true;

  // Toggle between login and register
  toggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const formType = btn.dataset.form;
      isLogin = formType === 'login';
      
      // Update active button
      toggleBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      // Show/hide fields based on form type
      nameGroup.classList.toggle('hidden', isLogin);
      emailGroup.classList.toggle('hidden', isLogin);
      usernameGroup.classList.toggle('hidden', !isLogin);
      passwordHint.classList.toggle('hidden', isLogin);
      
      // Update submit button text
      submitBtn.innerHTML = `${isLogin ? 'Sign In' : 'Create Account'} <span class="arrow">→</span>`;
      
      // Clear form and errors
      form.reset();
      clearErrors();
    });
  });

  // Toggle password visibility
  togglePasswordBtn.addEventListener('click', () => {
    const passwordInput = document.querySelector('input[name="password"]');
    const type = passwordInput.type === 'password' ? 'text' : 'password';
    passwordInput.type = type;
    togglePasswordBtn.textContent = type === 'password' ? '👁️' : '👁️‍🗨️';
  });

  // Validate email
  function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  // Validate password
  function validatePassword(password) {
    // Only apply strict validation for registration
    if (isLogin) return [];
    
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    const errors = [];
    if (password.length < minLength) errors.push("at least 8 characters");
    if (!hasUpperCase) errors.push("an uppercase letter");
    if (!hasLowerCase) errors.push("a lowercase letter");
    if (!hasNumbers) errors.push("a number");
    if (!hasSpecialChar) errors.push("a special character");

    return errors;
  }

  // Show error message
  function showError(input, message) {
    const errorElement = input.parentElement.querySelector('.error-message') || 
                        input.parentElement.parentElement.querySelector('.error-message');
    if (errorElement) {
      errorElement.textContent = message;
    }
  }

  // Clear all errors
  function clearErrors() {
    document.querySelectorAll('.error-message').forEach(error => {
      error.textContent = '';
    });
  }

  // Set a cookie
  function setCookie(name, value, days) {
    let expires = "";
    if (days) {
      const date = new Date();
      date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
      expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
  }

  // Form submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrors();

    const formData = new FormData(form);
    let hasError = false;

    // Validate name for registration
    if (!isLogin && !formData.get('name').trim()) {
      showError(form.elements.name, 'Name is required');
      hasError = true;
    }

    // Validate email for registration
    if (!isLogin && !validateEmail(formData.get('email'))) {
      showError(form.elements.email, 'Please enter a valid email address');
      hasError = true;
    }
    
    // Validate username for login
    if (isLogin && !formData.get('username').trim()) {
      showError(form.elements.username, 'Username is required');
      hasError = true;
    }

    // Validate password
    const passwordErrors = validatePassword(formData.get('password'));
    if (passwordErrors.length > 0 && !isLogin) {
      showError(
        form.elements.password,
        `Password must contain ${passwordErrors.join(', ')}`
      );
      hasError = true;
    }

    if (!hasError) {
      try {
        // Convert formData to a regular object
        const formDataObj = {};
        formData.forEach((value, key) => {
          formDataObj[key] = value;
        });
        
        // Create the payload based on login or register
        const payload = {
          password: formDataObj.password
        };
        
        // Add different fields based on login type
        if (isLogin) {
          payload.username = formDataObj.username; // Use actual username for login
        } else {
          payload.username = formDataObj.name; // Use name as username for registration
          payload.email = formDataObj.email;   // Include email for registration
        }
        
        // Make API call to appropriate endpoint
        const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (response.ok) {
          // Handle successful login/registration
          if (isLogin) {
            // Store auth token in localStorage and cookie
            localStorage.setItem('authToken', data.token);
            localStorage.setItem('currentUser', JSON.stringify(data.user));
            
            // Set the auth cookie that the server checks
            setCookie('authToken', data.token, 7); // Cookie lasts 7 days
            
            // Redirect to home page
            window.location.href = '/';
          } else {
            // Registration success - switch to login
            toggleBtns[0].click(); // Click the login button
            showError(form.elements.username, 'Registration successful! Please login with your username.');
          }
        } else {
          // Handle error response
          const errorMessage = data.error || (isLogin ? 'Login failed' : 'Registration failed');
          showError(isLogin ? form.elements.username : form.elements.email, errorMessage);
        }
      } catch (error) {
        console.error('Auth error:', error);
        showError(isLogin ? form.elements.username : form.elements.email, 'An error occurred. Please try again.');
      }
    }
  });
});