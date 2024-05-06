import argparse
import requests

def login(username, password):
    # Send login request and return session object
    session = requests.Session()
    login_data = {'username': username, 'password': password}
    response = session.post('https://example.com/login', data=login_data)
    # Check if login was successful
    if response.status_code == 200:
        return session
    else:
        print("Login failed")
        return None

def fill_form(session, form_data):
    # Parse form data from form.txt
    # Fill the form fields and submit using session.post()

def main():
    parser = argparse.ArgumentParser(description='Automate form filling')
    parser.add_argument('username', type=str, help='Username for login')
    parser.add_argument('password', type=str, help='Password for login')
    args = parser.parse_args()

    session = login(args.username, args.password)
    if session:
        form_data = read_form_data('form.txt')
        fill_form(session, form_data)

if __name__ == '__main__':
    main()

