#!/bin/bash

# Website URL
website_url="https://example.com/login"

# Username and password
username="your_username"
password="your_password"

# Perform login
login_result=$(curl -s -c cookies.txt -b cookies.txt -d "username=$username" -d "password=$password" "$website_url")

# Check if login was successful
if [[ $login_result == *"Login successful"* ]]; then
    echo "Login successful!"
else
    echo "Login failed!"
fi
