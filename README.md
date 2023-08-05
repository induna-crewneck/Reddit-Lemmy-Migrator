# Reddit-Lemmy-Migrator
Python script to transfer subreddit subscriptions to Lemmy or Kbin

## What it does
This script is meant to make the switch from Reddit to Lemmy (or kbin) easier. These are the steps taken by the script:
1. Get a list of subscribed subreddits from your profile
2. Look for communities with the same name as your subreddits on lemmy (or kbin)
3. Joins the communities with your Lemmy account.

## Prerequisites
- [Python 3](https://realpython.com/installing-python/)
- Python modules: requests, beautifulsoup4, selenium.
   - To install them all at once, run `pip install requests beautifulsoup4 selenium`
- ChromeDriver: To install Chromedriver on Linux you can run `pip install chromedriver-autoinstaller`, on Mac you might need to run `sudo "/Applications/Python 3.10/Install Certificates.command"` (change the path according to your python version of just check your Applications folder). If using WSL you can refer to [this guide](https://www.gregbrisebois.com/posts/chromedriver-in-wsl2/) 
- Lemmy account. You can pick a server and create one though [join-lemmy.org](https://join-lemmy.org/instances)
- Reddit account. Note that your reddit account needs to be set to english for this to work.

## Usage
1. Download the script from this repo (doesn't matter where to).
   - Use `reddit-lemmy-migrator.py` for Lemmy and `reddit-kbin-migrator.py` for kbin
2. Run the script: Open your Terminal (Mac) or Command Console (Windows) and run `python3 reddit-lemmy-migrator.py` / `python3 reddit-kbin-migrator.py`
3. Follow the prompts. If you are subscribed to a lot of subreddits, be patient.
4. Done!

### Command line argumnts
#### DEBUG
If you are getting errors or just want to see more of what's happening, you can instead run `python3 reddit-lemmy-migrator.py debug` (works with kbin version, too)
#### Login
To login via command line you can use `login` followed by your login data. Syntax:
`reddit-lemmy-migrator.py login [Reddit username] [Reddit password] [Lemmy server] [Lemmy username] [Lemmy password]`
You can combine this with `debug` but debug needs to be first: `reddit-lemmy-migrator.py debug login [Reddit username]...`
(If you're using the kbin version, it's the same principle. Just use your kbin server and kbin login data)

## FAQ
### What is Lemmy?
Lemmy is a lot like reddit, but selfhosted, open-source and decentralized. This means no single company (like Reddit) can suddenly decide to mess with things. For more info visit [[join-lemmy.org](https://join-lemmy.org)
### What is Kbin?
Basically the same as Lemmy. For more info visit [kbin.pub](https://kbin.pub/)
### Why would I want to switch from Reddit?
In short and besides the points mentioned above, Reddit is limiting users and mods and slowly making more and more changes to the platform to maximize profiablity.
### Is it safe to put my username and password into this?
Your credentials won't be stored in any file by this script. They will not be transmitted to me or any 3rd party services/websites. They are used solely to log-in to reddit and lemmy respectively to get a list of your subscribed subreddits from reddit and to subscribe to the communities on lemmy/kbin.
#### Privacy
Your password won't be displayed when entering. 

## Known Issues
### Incomplete lemmy magazine
Some communities are found on lemmy.world and are accessible through Lemmy instances but can not be joined or even accessed through kbin.

Example 1: Amoledbackgrounds is found when searching though lemmy.world. It can be accessed by any Lemmy instance under AmoledBackgrounds@lemmy.world but when accessing though Kbin it says `The magazine from the federated server may be incomplete`. You can browse it but not join.

Example 2: 3amjokes is also found and accessible through Lemmy, but when trying to access it through Kbin it throws a straight-up `404 Not found`.

There is nothing I can do about that since it is a kbin-"issue".
