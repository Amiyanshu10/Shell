import mechanize

# Create a browser object
br = mechanize.Browser()

# Ignore robots.txt
br.set_handle_robots(False)

# Open the website
br.open("https://example.com/login")

# Select the form
br.select_form(nr=0)  # Assuming the login form is the first form on the page

# Fill in the login credentials
br.form['username'] = 'your_username'
br.form['password'] = 'your_password'

# Submit the form
br.submit()

# Check if login was successful
if br.geturl() == "https://example.com/dashboard":
    print("Login successful!")
else:
    print("Login failed.")
