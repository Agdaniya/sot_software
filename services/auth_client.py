import requests


class AuthClient:
    def __init__(self, api_key):
        self.api_key = api_key

    def sign_in(self, email, password):
        url = (
            "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
            f"?key={self.api_key}"
        )

        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        response = requests.post(url, json=payload)
        data = response.json()

        if response.status_code != 200:
            error = data.get("error", {}).get("message", "Login failed")
            raise Exception(error)

        return data
