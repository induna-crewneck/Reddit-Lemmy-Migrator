# Reddit-Lemmy-Migrator
Python script to transfer subreddit subscriptions to Lemmy

## What it does
This script is meant to make the switch from Reddit to Lemmy easier. These are the steps taken by the script:
1. Get a list of subscribed subreddits from your profile
2. Look for communities with the same name as your subreddits on lemmy
   - It checks if the community is available on lemmy.world and searches for the community across servers with the most subscribers. So if there is a community on lemmy.world but also one for example on lemmy.ml that has more subscribers, both will be used.
3. Joins the communities with your Lemmy account.

## Prerequisites
You will need Python 3 aswell as the modules requests, beautifulsoup4, selenium

## Usage
1. Download the script `reddit-lemmy-migrator.py` from this repo (doesn't matter where to).
2. Run the script `python3 reddit-lemmy-migrator.py`
3. Follow the prompts
4. Done!

## FAQ
### What is Lemmy?
Lemmy is a lot like reddit, but selfhosted, open-source and decentralized. This means no single company (like Reddit) can suddenly decide to mess with things. For more info visit (join-lemmy.org)[https://join-lemmy.org/]
### Why would I want to switch from Reddit to Lemmy?
In short and besides the points mentioned above, Reddit is limiting users and mods and slowly making more and more changes to the platform to maximize profiablity.
### Is it safe to put my username and password into this?
Your credentials won't be stored in any file by this script. They will not be transmitted to me or any 3rd party services/websites. They are used solely to log-in to reddit and lemmy respectively to get a list of your subscribed subreddits from reddit and to subscribe to the communities on lemmy.
#### Privacy
When entering your login data it will be displayed in cleartext, so don't do this in public if you're worried about people glancing at your passwords.
