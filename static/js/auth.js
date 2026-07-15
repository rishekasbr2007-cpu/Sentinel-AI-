document.addEventListener("DOMContentLoaded", () => {
  // Tab Switching
  const tabBtns = document.querySelectorAll(".tab-btn");
  const authForms = document.querySelectorAll(".auth-form");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      // Remove active from all tabs
      tabBtns.forEach(b => b.classList.remove("active"));
      // Add active to clicked tab
      btn.classList.add("active");

      // Hide all forms
      authForms.forEach(form => form.classList.add("hidden"));
      // Show target form
      const targetId = btn.getAttribute("data-target");
      document.getElementById(targetId).classList.remove("hidden");
    });
  });

  // Password Visibility Toggle
  const toggleBtns = document.querySelectorAll(".toggle-password");
  toggleBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      const input = document.getElementById(targetId);
      if (input.type === "password") {
        input.type = "text";
        btn.textContent = "🙈"; // Hide icon
        btn.setAttribute("aria-label", "Hide password");
      } else {
        input.type = "password";
        btn.textContent = "👁"; // Show icon
        btn.setAttribute("aria-label", "Show password");
      }
    });
  });

  // --- Validation Logic ---
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const passwordRegex = /^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+={}\[\]:;"'<>,.?/\\|`~-]).{8,}$/;

  function validateField(input, errorElement, condition, errorMessage) {
    if (condition) {
      errorElement.textContent = "";
      input.classList.remove("invalid");
      input.classList.add("valid");
      return true;
    } else {
      errorElement.textContent = errorMessage;
      input.classList.remove("valid");
      input.classList.add("invalid");
      return false;
    }
  }

  // Signup Validation
  const signupForm = document.getElementById("signup-form");
  const signupName = document.getElementById("signup-name");
  const signupEmail = document.getElementById("signup-email");
  const signupPassword = document.getElementById("signup-password");
  const signupConfirm = document.getElementById("signup-confirm");
  const signupSubmit = document.getElementById("signup-submit");

  function checkSignupValidity() {
    let isValid = true;
    
    // Name
    if (signupName.value.trim() === "") {
      isValid = false;
    }

    // Email
    if (!emailRegex.test(signupEmail.value)) {
      isValid = false;
    }

    // Password
    if (!passwordRegex.test(signupPassword.value)) {
      isValid = false;
    }

    // Confirm
    if (signupPassword.value !== signupConfirm.value || signupConfirm.value === "") {
      isValid = false;
    }

    signupSubmit.disabled = !isValid;
  }

  if (signupForm) {
    signupName.addEventListener("input", () => {
      validateField(signupName, document.getElementById("signup-name-error"), signupName.value.trim() !== "", "Name is required");
      checkSignupValidity();
    });

    signupEmail.addEventListener("input", () => {
      validateField(signupEmail, document.getElementById("signup-email-error"), emailRegex.test(signupEmail.value), "Please enter a valid email address");
      checkSignupValidity();
    });

    signupPassword.addEventListener("input", () => {
      validateField(signupPassword, document.getElementById("signup-password-error"), passwordRegex.test(signupPassword.value), "Requires 8+ chars, 1 uppercase, 1 number, 1 special character");
      // Re-check confirm password if it's already filled
      if (signupConfirm.value !== "") {
        validateField(signupConfirm, document.getElementById("signup-confirm-error"), signupPassword.value === signupConfirm.value, "Passwords do not match");
      }
      checkSignupValidity();
    });

    signupConfirm.addEventListener("input", () => {
      validateField(signupConfirm, document.getElementById("signup-confirm-error"), signupPassword.value === signupConfirm.value, "Passwords do not match");
      checkSignupValidity();
    });

    // Prevent default HTML5 validation bubbles to use our custom UI
    signupForm.addEventListener("invalid", (e) => {
        e.preventDefault();
    }, true);
  }

  // Login Validation (Basic)
  const loginForm = document.getElementById("login-form");
  const loginEmail = document.getElementById("login-email");
  const loginPassword = document.getElementById("login-password");
  const loginSubmit = document.getElementById("login-submit");

  function checkLoginValidity() {
    let isValid = true;
    if (!emailRegex.test(loginEmail.value) || loginPassword.value.trim() === "") {
      isValid = false;
    }
    // We don't strictly disable login button based on robust rules, just to allow attempts
    // but we can add basic feedback
  }

  if (loginForm) {
    loginEmail.addEventListener("input", () => {
      validateField(loginEmail, document.getElementById("login-email-error"), emailRegex.test(loginEmail.value), "Invalid email format");
      checkLoginValidity();
    });

    loginPassword.addEventListener("input", () => {
       validateField(loginPassword, document.getElementById("login-password-error"), loginPassword.value.length > 0, "Password is required");
       checkLoginValidity();
    });
  }

  // Submit Loading State
  authForms.forEach(form => {
    form.addEventListener("submit", (e) => {
      const submitBtn = form.querySelector('button[type="submit"]');
      const btnText = submitBtn.querySelector('.btn-text');
      const loader = submitBtn.querySelector('.loader');

      // Add loading state
      submitBtn.disabled = true;
      btnText.classList.add('hidden');
      loader.classList.remove('hidden');
      
      // We don't preventDefault so the form actually submits to the server
    });
  });
});
