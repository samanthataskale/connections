# Flask App Installation Guide

This guide will walk you through the steps required to install and run a Flask app from a GitHub repository. 

## Prerequisites

Before you start, you will need to have the following installed on your system:

- Python 3.6 or higher
- pip package manager

## Installation

1. Clone the repository to your local machine:

   ```
   git clone https://github.com/username/connections.git
   ```
   
2. Navigate to the cloned directory:

   ```
   cd connections
   ```
   
3. Create a virtual environment:

   ```
   python3 -m venv venv
   ```
   
4. Activate the virtual environment:

   ```
   source venv/bin/activate
   ```
   
5. Install the required packages:

   ```
   pip install -r requirements.txt
   ```
   
6. Set the environment variables:

   ```
   export FLASK_APP=app.py
   export FLASK_ENV=development
   ```
   
7. Run the app:

   ```
   flask run
   ```

8. Access the app by opening a web browser and navigating to `http://localhost:5000`.

That's it! You should now have the Flask app up and running on your local machine.
