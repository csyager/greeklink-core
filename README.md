# Greeklink-core
This repository represents the source code of the Greeklink web application.  This repository is licensed as open-source, and comprises our solution for a personal homepage for Greek organizations in college campuses, along with technologies designed to aid these organizations in their social event planning.

## Installation Instructions
To download our product, run the following code from your command line interface:  
```
git clone https://github.com/csyager/greeklink-core.git
cd greeklink-core
./start-up
```
This will clone this repository, then run our start-up.sh script.  This script will create a virtual environment to run our code in, install our requirements (listed in requirements.txt), reinstantiate the database and remove lingering migrations, then make migrations and migrate based on the current status of the models.py file.  It then collects static files and loads the default admin account into the database.

## Contributing
To make contributions, please first clone the repository and create a new branch.  Commit any changes that you make to your branch and open a pull request when finished. Please make sure that your pull request and the merged branch builds are passing on TravisCI, otherwise your pull requests may be rejected.  If your pull request is adding considerable functionality, please unit test these features in the tests.py file.  The thoroughness of your testing can be checked using coverage.py.  To test your code-coverage, run `./coverage.sh`.  This script will open an HTML report on your browser showing the coverage percentage of your tests.