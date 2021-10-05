# greeklink-core  
[![Build Status](https://travis-ci.com/csyager/greeklink-core.svg?branch=master)](https://travis-ci.com/csyager/greeklink-core)

This repository represents the source code of the Greek-Rho (formerly GreekLink) web application.  This repository is licensed as open-source, and comprises our solution for a personal homepage for Greek organizations and student clubs on college campuses, along with technologies designed to aid these organizations in their everyday operations.  The solutions we've designed (thus far) include recruitment tools for tracking potential new members hoping to join your organization, social tools for managing lists of invitees for events, file-sharing resources, communication among members, and event planning resources.  Future resources include a finance tool for managing dues payments and organizational budgets.  

Our goal is to provide a home base for organization executives to conduct the operation of these often large groups as well as for members to receive information that will ultimately enable the organization to pursue it's goals more effectively.

## Tech Stack
This app is built using Django, a Python MVC framework that makes building a server-supported web application straightforward.  Django includes a templating language, controller, and model layer over a variety of database engines.  We use Postgresql.  Our cloud architecture is built using AWS Elastic Beanstalk, which provisions EC2 and RDS instances, load balancers, target groups, S3 storage, and logging/monitoring to support the application.

## Installation Instructions
### Requirements
* Python 3.6
* git
* Docker
 
To install the project locally, run the following commands from your command line interface:
```
git clone https://github.com/csyager/greeklink-core.git
cd greeklink-core
```
## Dependencies
Included in this project is a script, `start-up.sh`.  This will initialize a python virtual environment, remove any applied migrations and media files, start a clean docker image running the local postgres database, apply migrations, collect static files, and load the starting fixtures with entires that will be necessary for interacting with the site.  In production, we use a practice called multitenancy that allows us to use subdomains and separate Postgres schemas so multiple organizations can share our server space.  The `start-up.sh` script will initialize a test tenant in your local database.

## Running Locally

To run Django's built-in webserver, run `python manage.py runserver`, and open your web browser and navigate to http://test.localhost:8000.  The start-up script configures an admin account, whose credentials are:  

username: "admin"  
password: "greeklink1"

Use these credentials to sign into the application and view changes made to the local code.

## Useful Scripts

Django comes with several boilerplate scripts, a few of which need to be adjusted slightly to support multitenancy.

* `python manage.py runserver` - starts the Django webserver locally
* `python manage.py tenant-command shell --schema=test` - starts the Django shell in the terminal, allowing you to view and interact with database objects in a Python environment.  The schema parameter should be set to whatever schema you're working with.
* `python manage.py makemigrations [app name]` - Compiles any changes made to models.py in an app.  Leaving the app name parameter empty compiles all of them.
* `python manage.py migrate_schemas` - migrates changes compiled by makemigrations into the database.
* `python manage.py collectstatic` - collects static files from each sub-directory and compiles them into the central /static directory.

## Contributing

### Raising Issues
Issues can be submitted via GitHub issues.  We use cards created in Issues to triage development work.  Please include a descriptive title and comment and the issue will be addressed as quickly as we can get to it.

### Committing Changes
Any contributions should be made to their own branch.  Once your contribution is complete, open a pull request and it will be reviewed.  Included in the project repository is a script, `./coverage.sh`.  Running this script will execute unit tests on testable code, and will open a coverage report in your browser (if it doesn't, the report can be found at htmlcov/index.html).  The following testing guidelines **must** be followed before your branch can be merged:
1. All tests must pass - this is enforced by TravisCI
2. All new features must be tested
3. The coverage percentage must not decrease due to your PR

If these criteria are satisfied and your code contributes meaningful features to the project, it should be approved and merged.
