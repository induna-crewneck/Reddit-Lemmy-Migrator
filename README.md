# Reddit-Lemmy-Migrator
Python script to transfer subreddit subscriptions to Lemmy or Kbin

## What it does
This script is meant to make the switch from Reddit to Lemmy (or kbin) easier. These are the steps taken by the script:
1. Get a list of subscribed subreddits from your profile
2. Look for communities with the same name as your subreddits on lemmy (or kbin)
   - It checks if the community is available on lemmy.world (or kbin.social) and searches for the community across servers with the most subscribers. So if there is a community on lemmy.world (or kbin.social) but also one for example on lemmy.ml that has more subscribers, both will be used.
3. Joins the communities with your Lemmy account.

## Prerequisites
- [Python 3](https://realpython.com/installing-python/)
- Python modules: requests, beautifulsoup4, selenium.
   - To install them all at once, run `pip install requests beautifulsoup4 selenium`
- Lemmy account. You can pick a server and create one though [join-lemmy.org](https://join-lemmy.org/instances)
- Reddit account. Note that your reddit account needs to be set to english for this to work.

## Usage
1. Download the script from this repo (doesn't matter where to).
   - Use `reddit-lemmy-migrator.py` for Lemmy and `reddit-kbin-migrator.py` for kbin
2. Run the script: Open your Terminal (Mac) or Command Console (Windows) and run `python3 reddit-lemmy-migrator.py` / `python3 reddit-kbin-migrator.py`
3. Follow the prompts. If you are subscribed to a lot of subreddits, be patient.
4. Done!

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
When entering your login data it will be displayed in cleartext, so don't do this in public if you're worried about people glancing at your passwords.
