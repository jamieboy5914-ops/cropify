// Function to handle the response from the backend
function handleResponse(response) {
    if (response.success) {
        alert("User created successfully. Redirecting to login page...");
        // Redirect to login page after 5 seconds
        setTimeout(function() {
            window.location.href = "/login.html"; // Redirect to login page
        }, 5000); // 5000 milliseconds = 5 seconds
    } else {
        alert("Error: " + response.error); // Display error message
    }
}

// Function to handle form submission
function submitForm() {
    // Your form submission logic here
    // Example using fetch API
    fetch('/signup', {
        method: 'POST',
        body: new FormData(document.getElementById('signupForm')), // Assuming your form has id="signupForm"
    })
    .then(response => response.json())
    .then(data => handleResponse(data))
    .then()
    .catch(error => console.error('Error:', error));
}
