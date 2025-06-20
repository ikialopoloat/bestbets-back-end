document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const registrationForm = document.getElementById('registration-form'); // Assuming your registration form has this ID
    // Add a reference to the username input on the registration page
    const regUsernameInput = document.getElementById('username'); 
    
    let currentUserToken = null; // Global variable to store the ID token

    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();

            const email = emailInput.value;
            const password = passwordInput.value;

            firebase.auth().signInWithEmailAndPassword(email, password)
                .then((userCredential) => {
                    // Signed in
                    const user = userCredential.user;
                    console.log('User signed in successfully, getting ID token...');
                    return user.getIdToken();
                })
                .then((idToken) => {
                    console.log('ID Token obtained:', idToken);
                    currentUserToken = idToken; // Store the ID token
                    // Send the ID token to the backend for verification
                    return fetch('/verify-token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ idToken: idToken }),
                    });
                })
                .then((response) => {
                    if (response.ok) {
                        console.log('Token verified on backend. Redirecting to homepage...');
                        window.location.href = '/homepage'; // Redirect to the homepage
                    } else {
                        return response.json().then(error => { throw new Error(error.error || 'Token verification failed'); });
                    }
                })
                .catch((error) => {
                    const errorCode = error.code;
                    const errorMessage = error.message;
                    console.error('Error signing in:', errorCode, errorMessage);
                    // Display error message to the user
                    // const errorMessageElement = document.getElementById('error-message');
                    // if (errorMessageElement) {
                    //     errorMessageElement.textContent = errorMessage;
                    // }
                });
        });
    }

    if (registrationForm) {
        registrationForm.addEventListener('submit', function(event) {
            event.preventDefault();

            const email = document.getElementById('email').value; // Get email from registration form
            const password = document.getElementById('password').value; // Get password from registration form
            const confirmPassword = document.getElementById('confirm_password').value; // Get confirm password

            if (password !== confirmPassword) {
                alert("Passwords do not match!");
                return;
            }
            console.log(email, password)
            firebase.auth().createUserWithEmailAndPassword(email, password)
                .then((userCredential) => {
                    // Signed up
                    const user = userCredential.user; // Get the created user object
                    const username = regUsernameInput.value; // Get the username from the form

                    // Add the username and UID to Firestore
                    return firebase.firestore().collection('users').doc(user.uid).set({
                        username: username,
                        uid: user.uid
                    });
                })
                .then(() => {
                    console.log('User registered successfully and data added to Firestore.');
                    // You can redirect the user or display a success message here
                    window.location.href = '/'; // Redirect to login page after successful registration
                })
                .catch((error) => {
                    // Handle errors from both createUserWithEmailAndPassword and Firestore set
                    
                    const errorCode = error.code;
                    const errorMessage = error.message;
                    console.error('Error registering user:', errorCode, errorMessage);
                    alert(`Registration failed: ${errorMessage}`); // Display error message
                });
        });
    }

});

// Function to fetch a protected resource with the ID token
function fetchProtectedResource() {
    if (!currentUserToken) {
        console.error('No user token available. Please sign in.');
        return;
    }

    fetch('/protected-resource', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${currentUserToken}`
        }
    })
    .then(response => response.text()) // or response.json() if your protected resource returns JSON
    .then(data => console.log('Protected resource data:', data))
    .catch(error => console.error('Error fetching protected resource:', error));
}