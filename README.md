## How to Install

You need Python 3.8 and pipenv:
```bash
$ sudo apt install pipenv 
#linux
$ pip install pipenv
#windows
```
inside the project folder run-
```bash
$ pipenv shell
$ pipenv install --ignore-pipfile
# will install all required packages from pipfile.lock
```

## How to Run
Download chromedriver for your operating system from https://chromedriver.chromium.org/downloads

change the cromedriver path to your system in the below line in both project1.py and project2.py -

`driver = webdriver.Chrome(<Your chromedriver PATH>, options=chrome_options)`

Afterwards, run the py script.
After scraping the data, the script will open a popup window to authenticate to google drive.
You should login to your google account.

**Your drive should contain a spreadsheet called 'Food Panda'** for the script to successfully push the data into it.
