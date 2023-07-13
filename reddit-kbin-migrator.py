"""
Reddit to kbin migration assistant		v.1.3 (20230713)
	New changes:
	-Fixed reddit login check (used to proceed if credentials were wrong)
	-Fixed lemmy login (used to throw error due to username not being cleared on fail)
	-Added debug argument functionality
	-Simplified & optimised Lemmy community search
	-Discovered and added more info on Known Issue: 'Incomplete lemmy magazine'. Check Github page for more info
	-Added login through command line functionality

https://github.com/induna-crewneck/Reddit-Lemmy-Migrator/

This script is meant to automate migration from Reddit to kbin by getting a list of 
your subscribed subreddits, looking for them on kbin and subscribing to them there.

python3
"""

DEBUG = 0		# can be changed manually or activated by using "-debug" argument when executing the script:
				# "reddit-lemmy-migrator.py -debug"

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
import operator

# VARIABLES ------------------------------------------------------------------------------
reddURL = "https://old.reddit.com/subreddits/"
reddcredstatus = "not set"
kbinserverstatus = "not set"
kbincredstatus = "not set"
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
			redduname,reddpass,kbinserver,kbinuname,kbinpass = arglogindata
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

def getkbinserver():
	kbinserver = input("kbin instance:		")
	return kbinserver
	
def getkbinlogin():
	kbinuname = input("kbin username:		")
	kbinpass = input("kbin password:		")
	return kbinuname,kbinpass

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

def checkkbinserver(kbinserver):
	print("	Selected kbin server",end="")
	try:	
		s = requests.session()
		response = s.get("http://"+str(kbinserver))
		responsecode = int(str(re.findall(r"\d{3}", str(response)))[2:5])
		if responsecode != 200:
			print(" can't be accessed. Try again")
			status = "false_server"
			return status
		elif DEBUG == 1 :
			print(" can be accessed",end="")
		if "kbin" in response.text:
			print(" and seems to be a valid kbin instance.")
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
	
def checkkbinlogin(kbinserver,kbinuname,kbinpass):
	print("	kbin login data",end="")
	try:
		driver.get("http://"+kbinserver+"/login")
		driver.find_element("id", "email").clear()		#Clearing field to prepare for new username (in case of fail)
		driver.find_element("id", "email").send_keys(kbinuname)
		driver.find_element("id", "password").send_keys(kbinpass)
		driver.find_element(By.XPATH, '//*[@id="remember"]').click()
		driver.find_element(By.XPATH, '//*[@id="content"]/div/form/div[4]/button').click()
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

def socialcheck(sub):
	s = requests.session()
	response = s.get("https://kbin.social/m/"+sub)
	responsecode = int(str(re.findall(r"\d{3}", str(response)))[2:5])
	if responsecode == 200:
		#if DEBUG == 1 : print("found on kbin.social")
		socialresult = sub
	else:
		#print("not found on kbin.social")
		return 0
	file_object = open('kbin.txt', 'a')
	file_object.write("\n"+str(socialresult))
	file_object.close()
	return 1

def kbinsubsearch(sub):
	try:
		kbinsearchURL = "https://kbin.social/magazines?q="+sub
		driver.get(kbinsearchURL)
		results = driver.find_element(By.XPATH, '//*[@id="content"]/div/div/table')
		topkbinresult = driver.find_element(By.XPATH, '//*[@id="content"]/div/div/table/tbody/tr[1]/td[1]/a')
		if "@" in topkbinresult.text: topkbinresult = topkbinresult.text
		else: topkbinresult = topkbinresult.text
		#print("			result with most kbin subscribers: "+topkbinresult)
		if sub not in topkbinresult: return 0
		file_object = open('kbin.txt', 'a')
		file_object.write("\n"+str(topkbinresult))
		file_object.close()
		return 1
	except Exception as e:
		#if DEBUG == 1 : print("kbinsubsearch ERROR: ",e)
		return 0

def lemmysubsearch(sub):
	try:
		lemmysearchURL = "https://lemmy.world/search?q="+sub+"&type=Communities&sort=TopAll"
		driver.get(lemmysearchURL)
		topresult = driver.find_element(By.XPATH,'//*[@id="app"]/div[2]/div/div/div[3]/div/span[1]/a/span').text
		try:
			topresult = str(topresult)
		except:
			topresult=topresult
		if "@" not in topresult:
			topresult = topresult+"@lemmy.world"
			s = requests.session()
			response = s.get("http://"+str(kbinserver)+"/"+topresult)
			responsecode = int(str(re.findall(r"\d{3}", str(response)))[2:5])
			if responsecode != 200 and DEBUG == 1: print("not accessible\n			Check 'Incomplete lemmy magazine' under 'Known Issues' on the Github page for more info\n			Otherwise ",end="")
			return 0
		file_object = open("kbin.txt", "a")
		file_object.write("\n"+topresult)
		file_object.close()
		return 1
	except NoSuchElementException:
		return 0
	except Exception as e:
		if DEBUG == 1 : print(" produced an error: ",e)
		return 0

def cleankbin():
	try:
		lines_seen = set()
		outfile = open("kbin2.txt", "w")
		for line in open("kbin.txt", "r"):
			if line not in lines_seen and " " not in line:
				outfile.write(line)
				lines_seen.add(line)
		outfile.close()
		os.remove("kbin.txt")
		os.rename("kbin2.txt","kbin.txt")
	except Exception as e:
		if DEBUG == 1 : print(e)

def kbinjoin():
	try:
		with open("kbin.txt","r") as f:
			data = f.readlines()
			for line in data:
				line = str(line).strip()
				if line == "None": line = ""
				if len(line) >= 1:
					if "@" in line: print("	"+line,end="")
					else: print("	"+line+"@kbin.social",end="")
					try:
						driver.get("https://"+kbinserver+"/m/"+line)
						time.sleep(1)
						kbinBTN = driver.find_element(By.XPATH, '//*[@id="sidebar"]/section[1]/aside/form[1]/button')
						if kbinBTN.text == "Subscribe":
							kbinBTN.click()
							print(" subscribed")
						elif kbinBTN.text == "Unsubscribe":
							print(" already subsribed")
						else:
							print(" not subscribed (ERROR 1)")
					except Exception as e2:
						print(" not subscribed (ERROR 2)")
						if DEBUG == 1 : print(e2)
		os.remove("kbin.txt")
	except Exception as e:
		print("	Error while joining kbin communities.")
		if DEBUG == 1 : print(e)
		exit()

# EXECUTION ------------------------------------------------------------------------------
print("Welcome to the Reddit to Kbin migration tool.\n")
print("It will create a list of your subscribed subreddits, look for communities with the same name on kbin")
print("and subscribe to the community with the most subscribers. If there is a community on kbin.social that is")
print("not the one with the most subscribers, it will still be subscribed to.\n")

if ARGLOGIN == 1:
	if DEBUG == 1: print("Login data received from command line arguments\n	Checking login data")
	reddcredstatus = checkreddlogin(redduname,reddpass)
	if DEBUG == 1 and reddcredstatus != "OK": print("		Reddit credentials in command line arguments seem to be incorrect")
	kbinserverstatus = checkkbinserver(kbinserver)
	if DEBUG == 1 and kbinserverstatus != "OK": print("		Lemmy instance in command line arguments seems to be incorrect")
	kbincredstatus = checkkbinlogin(kbinserver,kbinuname,kbinpass)
	if DEBUG == 1 and kbincredstatus != "OK": print("		Lemmy credentials in command line arguments seem to be incorrect")

if ARGLOGIN == 0: print("Please enter your Reddit account info")

while reddcredstatus != "OK":
	redduname,reddpass = getredditlogin()
	reddcredstatus = checkreddlogin(redduname,reddpass)

if ARGLOGIN == 0: print("\nPlease enter your kbin account info ('instance' is the server you signed-up on, like kbin.social)")
while kbinserverstatus != "OK":
	kbinserver = getkbinserver()
	kbinserverstatus = checkkbinserver(kbinserver)

while kbincredstatus != "OK":
	kbinuname,kbinpass = getkbinlogin()
	kbincredstatus = checkkbinlogin(kbinserver,kbinuname,kbinpass)

print("Getting a list of your subsribed subreddits")
subs = getsubs()

subs = ['3amjokes','AmoledBackgrounds','collegehumor','me_irl','testestestafddas']
kbinserver = "kbin.social"

print("	Looking for corresponding communities on kbin. Depending on the number of subreddits, this can take a while.")
for sub in subs:
	sub = str(sub)
	if DEBUG == 1 : print("		"+sub+" ",end="")
	try:
		socialresult = socialcheck(sub)
		topkbinresult = kbinsubsearch(sub)
		lemmyresult = lemmysubsearch(sub)
		if DEBUG == 1:
			if socialresult + topkbinresult + lemmyresult == 0: print("not found")
			else: print("found")
	except Exception as e3:
		if DEBUG == 1 : print("ERROR while searching: ",e3)

time.sleep(999) #debug

print("Cleaning up duplicates")
cleankbin()

print("\nJoining kbin communities")
kbinjoin()

driver.quit()
print("\nProcess finished.")