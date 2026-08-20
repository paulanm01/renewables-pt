from app import create_app

# The Flask development server and CLI tools look for a variable
# named 'app' in this file.
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)