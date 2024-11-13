document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("submit-btn-login").addEventListener("click", async (event) => {
        const errorMessageContainer = document.getElementById("error-message");
        const username = document.getElementById("username-tb-login").value;
        const password = document.getElementById("pass-tb-login").value;

        event.preventDefault();

        if (!username || !password) {
            errorMessageContainer.style.display = 'block';
            errorMessageContainer.style.color = 'red';
            errorMessageContainer.textContent = "Please enter both username and password.";
            errorMessageContainer.style.textAlign = "center";
            return;
        }

        try {
            const loginData = await log_in();
            const response = await sendLoginRequest(loginData);
            const responseData = await response.json();

            if (response.ok) {
                const token = responseData.access_token;

                if (token) {
                    localStorage.setItem('access_token', token);
                    console.log("Token saved to localStorage");

                    errorMessageContainer.style.display = 'block';
                    errorMessageContainer.style.textAlign = "center";
                    errorMessageContainer.textContent = "Successful Entry";
                    errorMessageContainer.style.color = 'green';

                    setTimeout(() => {
                        window.location.href = "http://127.0.0.1:3000/CLIENT";
                    }, 3000);
                } else {
                    console.error("No token received in response");
                    errorMessageContainer.style.display = 'block';
                    errorMessageContainer.style.textAlign = "center";
                    errorMessageContainer.textContent = "No token received. Please try again.";
                    errorMessageContainer.style.color = 'red';
                }
            } else {
                console.error("Failed to authenticate:", responseData);
                errorMessageContainer.style.display = 'block';
                errorMessageContainer.style.textAlign = "center";
                errorMessageContainer.textContent = responseData.detail;
                errorMessageContainer.style.color = 'red';
            }

        } catch (error) {
            console.error("Error during login request:", error);
            errorMessageContainer.style.display = 'block';
            errorMessageContainer.textContent = "An error occurred. Please try again later.";
            errorMessageContainer.style.color = 'red';
        }
    });


    document.getElementById("submit-btn-reg").addEventListener("click", async (event) => {
        const errorMessageContainer_reg = document.getElementById("error-message-reg");
        errorMessageContainer_reg.textContent = "";
        const username = document.getElementById("username-tb").value;
        const email = document.getElementById("email-tb-reg").value;
        const pass = document.getElementById("pass-tb-reg").value;
        const pass_again = document.getElementById("pass-tb-reg-again").value;

        event.preventDefault();

        if (pass != pass_again) {
            errorMessageContainer_reg.style.display = 'block';
            errorMessageContainer_reg.textContent = "Passwords are not the same.";
            errorMessageContainer_reg.style.color = 'red';
            errorMessageContainer_reg.style.textAlign = "center"
            return
        }

        if (!username || !email || !pass || !pass_again) {
            errorMessageContainer_reg.style.display = 'block';
            errorMessageContainer_reg.style.color = 'red';
            errorMessageContainer_reg.textContent = "Please fill the gaps!";
            errorMessageContainer_reg.style.textAlign = "center";
            return;
        }


        try {
            const registerData = await register();
            const response = await sendRegisterRequest(registerData);
            const responseData = await response.json();

            if (response.ok) {
                errorMessageContainer_reg.style.display = 'block';
                errorMessageContainer_reg.style.textAlign = "center";
                errorMessageContainer_reg.textContent = responseData.message;
                errorMessageContainer_reg.style.color = 'green';
            }
            else {
                errorMessageContainer_reg.style.display = 'block';
                errorMessageContainer_reg.textContent = responseData.detail;
                errorMessageContainer_reg.style.color = 'red';
                errorMessageContainer_reg.style.textAlign = "center"
                return
            }

        } catch {
            console.error("Error during login request:", error);
            errorMessageContainer_reg.style.display = 'block';
            errorMessageContainer_reg.textContent = "An error occurred. Please try again later.";
            errorMessageContainer_reg.style.color = 'red';
        }


    })
});


async function sendLoginRequest(data) {
    const urlEncodedData = new URLSearchParams(data).toString();
    const response = await fetch('http://localhost:8000/auth/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: urlEncodedData
    });
    return response;
}

async function sendRegisterRequest(data) {
    const response = await fetch('http://localhost:8000/auth', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    return response;
}

async function sendGoogleAuthRequest(data) {
    const response = await fetch('http://localhost:8000/social_auth/google', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });

    return response;
}

async function log_in() {
    let username = document.getElementById("username-tb-login").value;
    let password = document.getElementById("pass-tb-login").value;
    let data = { "username": username, "password": password };
    return data;
}

async function register() {
    let username = document.getElementById("username-tb").value;
    let email = document.getElementById("email-tb-reg").value;
    let password = document.getElementById("pass-tb-reg").value;
    let is_organizer = document.getElementById("is_organizer").checked ? 1 : 0;

    let data = {
        "username": username,
        "email": email,
        "password": password,
        "first_name": "string",
        "last_name": "string",
        "is_organizer": is_organizer
    };
    return data;
}

async function google_auth(payload) {
    let data = {
        "id" : payload["sub"],
        "email" : payload["email"],
        "picture" : payload["picture"],
        "provider" : "google"
    }
    if(payload["given_name"]){
        data["first_name"] = payload["given_name"];
    }else{
        data["first_name"] = "";
    }

    if(payload["family_name"]){
        data["last_name"] = payload["family_name"];
    }else{
        data["last_name"] = "";
    }

    if(payload["name"]){
        data["display_name"] = payload["name"];
    }else {
        data["display_name"] = "";
    }

    return data
}

async function handleCredentialResponse(response) {
    const errorMessageContainer = document.getElementById("error-message");
    var tokens = response.credential.split(".");
    var payload = JSON.parse(atob(tokens[1]));  

    try {
        const googleAuthData = await google_auth(payload);
        const response = await sendGoogleAuthRequest(googleAuthData);
        const responseData = await response.json();
        
        if (response.ok) {
            const token = responseData.access_token;
            if (token) {
                localStorage.setItem('access_token', token);
                console.log("Token saved to localStorage");

                errorMessageContainer.style.display = 'block';
                errorMessageContainer.style.textAlign = "center";
                errorMessageContainer.textContent = "Successful Entry";
                errorMessageContainer.style.color = 'green';

                setTimeout(() => {
                    window.location.href = "http://127.0.0.1:3000/CLIENT";
                }, 3000);
            } else {
                console.error("No token received in response");
                errorMessageContainer.style.display = 'block';
                errorMessageContainer.style.textAlign = "center";
                errorMessageContainer.textContent = "No token received. Please try again.";
                errorMessageContainer.style.color = 'red';
            }
        } else {
            console.error("Failed to authenticate:", responseData);
            errorMessageContainer.style.display = 'block';
            errorMessageContainer.style.textAlign = "center";
            errorMessageContainer.textContent = responseData.detail;
            errorMessageContainer.style.color = 'red';
        }

    } catch (error) {
        console.error("Error during login request:", error);
        errorMessageContainer.style.display = 'block';
        errorMessageContainer.textContent = "An error occurred. Please try again later.";
        errorMessageContainer.style.color = 'red';
    }
}

window.onload = function () {

    google.accounts.id.initialize({
        client_id: "1054962718888-1q0f5m7hbnqjkvo241mj7jbhh5ljmji2.apps.googleusercontent.com",
        callback: handleCredentialResponse
    });
    google.accounts.id.renderButton(
        document.getElementById("buttonDiv"),
        { theme: "outline", size: "large" }  // customization attributes
    );
    google.accounts.id.prompt(); // also display the One Tap dialog
}
