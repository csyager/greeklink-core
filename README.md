# Greeklink-core  
[![Build Status](https://travis-ci.com/csyager/greeklink-core.svg?branch=master)](https://travis-ci.com/csyager/greeklink-core)  

This repository represents the source code of the Greeklink web application.  This repository is licensed as open-source, and comprises our solution for a personal homepage for Greek organizations in college campuses, along with technologies designed to aid these organizations in their social event planning.

## Installation Instructions
### Linux
To download our product, run the following code from your command line interface:  
```
git clone https://github.com/csyager/greeklink-core.git
cd greeklink-core
```
For some functionality, as well as to protect secret keys, we use a .env file.  This file is stored in the greeklink_core directory.  Use a text editor to open the .env-template file (note that the file may be hidden).  Change the line that starts with `DJANGO_SECRET_KEY=` to store a 50-character secret key for your app.  When this is done, change the name of the file from .env-template to .env, navigate back to the main directory, and run:

```
./start-up.sh
source env/bin/activate
```

This will run our start-up.sh script.  This script will create a virtual environment to run our code in, install our requirements (listed in requirements.txt), reinstantiate the database and remove lingering migrations, then make migrations and migrate based on the current status of the models.py file.  It then collects static files and loads the default admin account into the database.

To run Django's built-in webserver, run `python manage.py runserver`, and open your web browser and navigate to http://localhost:8000.  The Greeklink-core site comes packaged with an admin account, whose credentials are:  

username: "admin"
password: "greeklink1"

Use these credentials to sign into the application and view changes made to the local code.

## Contributing
To make contributions, please first clone the repository and create a new branch.  Commit any changes that you make to your branch and open a pull request when finished. Please make sure that your pull request and the merged branch builds are passing on TravisCI, otherwise your pull requests may be rejected.  If your pull request is adding considerable functionality, please unit test these features in the tests.py file.  The thoroughness of your testing can be checked using coverage.py.  To test your code-coverage, run `./coverage.sh`.  This script will open an HTML report on your browser showing the coverage percentage of your tests.
