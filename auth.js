let isLoginMode = true;

document.getElementById('toggleMode').addEventListener('click', (e) => {
    e.preventDefault();
    isLoginMode = !isLoginMode;
    document.getElementById('authTitle').innerText = isLoginMode ? 'Sign In' : 'Create Account';
    document.getElementById('submitBtn').innerText = isLoginMode ? 'Login' : 'Register';
    document.getElementById('toggleMode').innerText = isLoginMode ? 'Need an account? Register here' : 'Already have an account? Sign in';
    document.getElementById('errorMsg').innerText = '';
});

document.getElementById('authForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    const errorEl = document.getElementById('errorMsg');
    const submitBtn = document.getElementById('submitBtn');
    
    errorEl.innerText = '';
    submitBtn.disabled = true;

    try {
        if (!isLoginMode) {
            // Register
            const regRes = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user, password: pass })
            });
            
            if (!regRes.ok) {
                const err = await regRes.json();
                throw new Error(err.detail || "Registration failed");
            }
        }
        
        // Login
        const formData = new URLSearchParams();
        formData.append('username', user);
        formData.append('password', pass);
        
        const loginRes = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });
        
        if (!loginRes.ok) {
            const err = await loginRes.json();
            throw new Error(err.detail || "Login failed");
        }
        
        const data = await loginRes.json();
        localStorage.setItem('token', data.access_token);
        
        // Redirect to dashboard
        window.location.href = '/';
        
    } catch (err) {
        errorEl.innerText = err.message;
    } finally {
        submitBtn.disabled = false;
    }
});
