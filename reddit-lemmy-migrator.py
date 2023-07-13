"""
Reddit to Lemmy migration assistant		v.1.3 (20230713)
	New changes:
	-Fixed reddit login check (used to proceed if credentials were wrong)
	-Added debug argument functionality
	-Simplified & optimised Lemmy community search. Now only does one search across instances
	-Changed Lemmy list cleaning behaviour
	-Added login through command line functionality

https://github.com/induna-crewneck/Reddit-Lemmy-Migrator/

This script is meant to automate migration from Reddit to kbin by getting a list of 
your subscribed subreddits, looking for them on kbin and subscribing to them there.

python3
"""

DEBUG = 0		# can be changed manually or activated by using "debug" argument when executing the script:
				# "reddit-lemmy-migrator.py debug"

# IMPORTS --------------------------------------------------------------------------------
import sys
from bs4 import BeautifulSoup 
import requests
import re
import time
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import os

# VARIABLES ------------------------------------------------------------------------------
reddURL = "https://old.reddit.com/subreddits/"
reddcredstatus = "not set"
lemmyserverstatus = "not set"
lemmycredstatus = "not set"
ARGLOGIN = 0

# Setting DEBUG if "-debug was added to command-line"
try:
	sysarg = sys.argv[1].replace("-","")
	if "debug" in sysarg:
		DEBUG = 1
		print("\nDEBUG output enabled by user")
	if "help" in sysarg:
		print("\nInfo about program:		github.com/induna-crewneck/Reddit-Lemmy-Migrator")
		print("To enable debug info output use 'debug'")
		print("To login via command line you can use 'login' followed by your login data. Syntax:\n	reddit-lemmy-migrator.py login [Reddit username] [Reddit password] [Lemmy server] [Lemmy username] [Lemmy password]")
		exit()
	if "login" in str(sys.argv):
		try:
			ARGLOGIN = 1
			arglogindata = str(re.findall('login (.*)', " ".join(sys.argv))).replace("'","").replace("[","").replace("]","").split(" ")
			redduname,reddpass,lemmserver,lemmuname,lemmpass = arglogindata
		except Exception as e2:
			ARGLOGIN = 0
			if DEBUG == 1: print("Error processing login data from arguments: "+str(e2))
	if DEBUG == 1: print("\n")
except Exception as e:
	if DEBUG == 1: print("no arguments added to execution command "+e)

# PRE-SETUP ------------------------------------------------------------------------------
chrome_options = Options()
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
if DEBUG != 1: chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)

# GET LOGIN DATA -------------------------------------------------------------------------
def getredditlogin():
	redduname = input("Reddit username:	")
	reddpass = input("Reddit password:	")
	return redduname, reddpass

def getlemmyserver():
	lemmserver = input("Lemmy instance:		")
	return lemmserver
	
def getlemmylogin():
	lemmuname = input("Lemmy username:		")
	lemmpass = input("Lemmy password:		")
	return lemmuname,lemmpass

def checkreddlogin(redduname,reddpass):
	if DEBUG == 1 : print("	Checking Reddit login data")
	try:
		driver.get(reddURL)
		driver.find_element(By.XPATH, '//*[@id="login_login-main"]/input[2]').send_keys(redduname)
		driver.find_element("id", "rem-login-main").click()
		driver.find_element(By.XPATH, '//*[@id="login_login-main"]/input[3]').send_keys(reddpass)
		driver.find_element(By.XPATH, '//*[@id="login_login-main"]/div[4]/button').click()
		time.sleep(3)
		try:
			loginstatus = driver.find_element(By.XPATH,'//*[@id="login_login-main"]/div[2]').text
			if DEBUG == 1 and loginstatus != "incorrect username or password": print("		"+loginstatus)
			print("	Incorrect username or password")
			return "false_login"
		except NoSuchElementException:
			if DEBUG == 1 : print("		Login error not found (this is good)")
			print("	Reddit login success")
			return "OK"
		except Exception as e2:
			if DEBUG == 1 : print("		Error while checking Reddit credentials:\n"+e2)
	except Exception as e:
		if DEBUG == 1 : print("		Error while checking Reddit credentials:\n"+e)
		print(" Reddit login could not be verified due to an error.")
		return "false_login"

def checklemmyserver(lemmserver):
	print("	Selected Lemmy server",end="")
	try:	
		s = requests.session()
		response = s.get("http://"+str(lemmserver))
		responsecode = int(str(re.findall(r"\d{3}", str(response)))[2:5])
		if responsecode != 200:
			print(" can't be accessed. Try again")
			status = "false_server"
			return status
		elif DEBUG == 1 :
			print(" can be accessed",end="")
		if "lemmy" in response.text:
			print(" and seems to be a valid Lemmy instance.")
			status = "OK"
			return status
		else:
			print(" but doesn't seem to be valid. Try again.")
			status = "false_server"
			return status
	except Exception as e:
		print(" not working. Try again.")
		if DEBUG == 1 : print(e)
		status = "false_server"
		return status
	
def checklemmylogin(lemmserver,lemmuname,lemmpass):
	print("	Lemmy login data",end="")
	try:
		driver.get("http://"+lemmserver+"/login")
		driver.find_element("id", "login-email-or-username").send_keys(lemmuname)
		driver.find_element("id", "login-password").send_keys(lemmpass)
		driver.find_element("id", "login-password").send_keys(Keys.ENTER)
		time.sleep(5)
		currentURL = driver.current_url
		if "login" in currentURL:
			print(" wrong. Try again.")
			status = "false_login"
			return status
		print(" valid.")
		status = "OK"
		return status
	except Exception as e:
		print(" could not be verified due to an error.")
		if DEBUG == 1 : print(e)
		status = "false_login"
		return status

# PROCESSING -----------------------------------------------------------------------------
def getsubs():
	try:
		driver.get(reddURL)
		multi = driver.find_element(By.LINK_TEXT, "multireddit of your subscriptions").get_attribute('href')
	except Exception as e:
		print("	Error obtaining subreddit list\nMake sure your reddit account is set to english.")
		if DEBUG == 1 : print(e)
		exit()
	try:
		subs = multi.replace("https://old.reddit.com/r/","").split("+")
		print("	Found",len(subs),"subreddits")
		return subs
	except Exception as e:
		print("	Error processing subreddit list")
		if DEBUG == 1 : print(e)
		exit()

def lemmysubsearch(sub):
	try:
		lemmysearchURL = "https://lemmy.world/search?q="+sub+"&type=Communities&sort=TopAll"
		driver.get(lemmysearchURL)
		topresult = driver.find_element(By.XPATH,'//*[@id="app"]/div[2]/div/div/div[3]/div/span[1]/a/span').text
		try:
			topresult = str(topresult)
		except:
			topresult=topresult
		file_object = open("lemmy.txt", "a")
		file_object.write("\n"+topresult)
		file_object.close()
		return topresult
	except NoSuchElementException:
		return 0
	except Exception as e:
		if DEBUG == 1 : print(" produced an error: ",e)
		return 1

def lemmycleanup():
	try:
		lines_seen = set()
		outfile = open("lemmy2.txt", "w")
		for line in open("lemmy.txt", "r"):
			if line not in lines_seen:
				outfile.write(line)
				lines_seen.add(line)
		outfile.close()
		os.remove("lemmy.txt")
		os.rename("lemmy2.txt","lenny.txt")
	except Exception as e:
		if DEBUG == 1 : print(e)

def lemmyjoin():
	try:
		with open("lemmy.txt","r") as f:
			data = f.readlines()
			for line in data:
				line = str(line).strip()
				if len(line) >= 1:
					print("	"+line,end="")
					try:
						driver.get("https://"+lemmserver+"/c/"+line)
						time.sleep(1)
						LemmyBTN = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-secondary.d-block.mb-2.w-100")
						if LemmyBTN.text == "Subscribe":
							LemmyBTN.click()
							print(" subscribed")
						elif LemmyBTN.text == "Joined":
							print(" already subsribed")
						else:
							print(" not subscribed (ERROR 1)")
					except Exception as e2:
						print(" not subscribed (ERROR 2)")
						if DEBUG == 1 : print(e2)
		os.remove("lemmy.txt")
	except Exception as e:
		print("	Error while joining Lemmy communities.")
		if DEBUG == 1 : print(e)
		exit()

# EXECUTION ------------------------------------------------------------------------------
print("Welcome to the Reddit to Lemmy migration tool.\n")
print("It will create a list of your subscribed subreddits, look for communities with the same name on Lemmy")
print("and subscribe to the community with the most subscribers (searching through lemmy.world)\n")

if ARGLOGIN == 1:
	if DEBUG == 1: print("Login data received from command line arguments\n	Checking login data")
	reddcredstatus = checkreddlogin(redduname,reddpass)
	if DEBUG == 1 and reddcredstatus != "OK": print("		Reddit credentials in command line arguments seem to be incorrect")
	lemmyserverstatus = checklemmyserver(lemmserver)
	if DEBUG == 1 and lemmyserverstatus != "OK": print("		Lemmy instance in command line arguments seems to be incorrect")
	lemmycredstatus = checklemmylogin(lemmserver,lemmuname,lemmpass)
	if DEBUG == 1 and lemmycredstatus != "OK": print("		Lemmy credentials in command line arguments seem to be incorrect")

if ARGLOGIN == 0: print("Please enter your Reddit account info")

while reddcredstatus != "OK":
	redduname,reddpass = getredditlogin()
	reddcredstatus = checkreddlogin(redduname,reddpass)

if ARGLOGIN == 0: print("\nPlease enter your Lemmy account info ('instance' is the server you signed-up on, like lemmy.world)")
while lemmyserverstatus != "OK":
	lemmserver = getlemmyserver()
	lemmyserverstatus = checklemmyserver(lemmserver)
while lemmycredstatus != "OK":
	lemmuname,lemmpass = getlemmylogin()
	lemmycredstatus = checklemmylogin(lemmserver,lemmuname,lemmpass)

print("Getting a list of your subsribed subreddits")
subs = getsubs()

print("	Looking for corresponding communities on Lemmy. Depending on the number of subreddits, this can take a while.")
for sub in subs:
	sub = str(sub)
	if DEBUG == 1 : print("		"+sub,end="")
	try:
		lemmyresult = lemmysubsearch(sub)
		if DEBUG == 1:
			if lemmyresult == 0: print(" not found on Lemmy.")
			elif lemmyresult == 1 and DEBUG != 1 : print(" produced an Error while searching.")
			elif len(lemmyresult)>1: print("@"+lemmyresult.replace(sub,"").replace("@",""))
	except Exception as e:
		if DEBUG == 1 : print("\n")
		print("Error looking for "+sub+": "+e)

if DEBUG == 1 : print("	Cleaning up result list")
lemmycleanup()

print("\nJoining Lemmy communities")
lemmyjoin()

driver.quit()
print("\nProcess finished.")