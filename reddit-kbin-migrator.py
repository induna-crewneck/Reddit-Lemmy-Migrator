"""
Reddit to kbin migration assistant		v.1.6 (20230804)
	New changes:
	-sub.rehab implementation
		additionally to old method, also searches sub.rehab for subreddit substitute
	-sizeable UX overhaul
		-progress display for community search (disabled in DEBUG mode)
			-variation for DEBUG mode
		-stats at end
		-simplified output in normal and DEBUG mode
		-added spacing dots to make list outputs more cohesive
		-added custom messaging for common errors

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
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from getpass import getpass
import os
import operator

# VARIABLES ------------------------------------------------------------------------------
reddURL = "https://old.reddit.com/subreddits/"
reddcredstatus = "not set"
kbinserverstatus = "not set"
kbincredstatus = "not set"
ARGLOGIN = 0

searchpercent = 0
counter = 0
substitutes_found = 0

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
try:
	chromedriver_autoinstaller.install()
	chrome_options = Options()
	chrome_options.add_argument("--disable-extensions")
	chrome_options.add_argument("--disable-gpu")
	if DEBUG != 1: chrome_options.add_argument("--headless")
	driver = webdriver.Chrome(options=chrome_options)
except Expception as e:
	print("Error while setting up chromedriver")
	if DEBUG == 1: print(e)
	exit()

# GET LOGIN DATA -------------------------------------------------------------------------
def getredditlogin():
	redduname = input("Reddit username:	")
	reddpass = getpass("Reddit password:	")
	return redduname, reddpass

def getkbinserver():
	kbinserver = input("kbin instance:		")
	return kbinserver
	
def getkbinlogin():
	kbinuname = input("kbin username:		")
	kbinpass = getpass("kbin password:		")
	return kbinuname,kbinpass

def checkreddlogin(redduname,reddpass):
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

def subrehabsearch(sub):
	try:
		rehabURL = "https://sub.rehab/r/"+sub
		s = requests.session()
		response = s.get(rehabURL)
		results = re.findall('mantine-11qn4mn" href="([^\"]+)', str(response.text))
		if results:
			topresulturl = str(''.join(results[:1]))
			topresultinstance = str(''.join(re.findall('\/\/([^\/]+)',topresulturl)[:1]))
			topresultcommunity = str(''.join(re.findall('\/c\/([^\/]+)',topresulturl)[:1]))
			topresult = topresultcommunity.lower()+"@"+topresultinstance
			if "discord.gg" in topresult or "raddle" in topresult or "squabbles" in topresult or "ramble" in topresult: return 0,""	# discarding results on other platforms
			return 1,topresult
		else: return 0,""
	except Exception as e:
		if DEBUG == 1: print(str(e)[0:320])
		return 0,""

def kbinsubsearch(sub):
	try:
		kbinsearchURL = "https://kbin.social/magazines?query="+sub+"&fields=names&federation=all&adult=show"
		driver.get(kbinsearchURL)
		topkbinresult = driver.find_element(By.XPATH, '//*[@id="content"]/div/div/table/tbody/tr[1]/td[1]/a').get_attribute('title')[1:]
		return 1,topkbinresult
	except Exception as e:
		return 0,""

def lemmysubsearch(sub):
	try:
		s = requests.session()
		response = s.get("http://lemmy.world/")
		responsecode = int(str(re.findall(r"\d{3}", str(response)))[2:5])
	except: responsecode = 0
	if responsecode != 200:
		try:
			s = requests.session()
			response = s.get("http://lemmy.ml/")
			responsecode = int(str(re.findall(r"\d{3}", str(response)))[2:5])
			if responsecode == 200: lemmserver = "lemmy.ml"
		except: responsecode = 0
	else: lemmserver = "lemmy.world"
	try:
		lemmysearchURL = "http://"+lemmserver+"/search?q="+sub+"&type=Communities&sort=TopAll"
		driver.get(lemmysearchURL)
		topresult = driver.find_element(By.XPATH,'//*[@id="app"]/div[2]/div/div/div[3]/div/span[1]/a').get_attribute('title').replace("!","")
		try: topresult = str(topresult)
		except: topresult = topresult
		try: topresult = topresult.replace(" ","")
		except: topresult = topresult
		topresult = topresult.lower()
		if "@" not in topresult:
			try: topresult = topresult+"@"+lemmserver
			except: topresult = topresult
		response2 = s.get("http://"+lemmserver+"/"+topresult)
		responsecode2 = int(str(re.findall(r"\d{3}", str(response2)))[2:5])
		if responsecode2 != 200: return 0,""
		return 1,topresult
	except NoSuchElementException:
		return 0,""
	except Exception as e:
		if DEBUG == 1 :
			try: print(" produced an error: "+str(e)[0:60])
			except: print(" produced an error: ",e)
		return 0,""

def cleankbin():
	substitutes = 0
	try:
		lines_seen = set()
		outfile = open("kbin2.txt", "w")
		for line in open("kbin.txt", "r"):
			if line not in lines_seen and " " not in line:
				outfile.write(line)
				substitutes = substitutes+1
				lines_seen.add(line)
		outfile.close()
		os.remove("kbin.txt")
		os.rename("kbin2.txt","kbin.txt")
		return substitutes
	except Exception as e:
		if DEBUG == 1 : print(e)

def kbinjoin(substitutes):
	try:
		counter = 0
		subscribed = 0
		already = 0
		notsubbed = 0
		pending = 0
		with open("kbin.txt","r") as f:
			data = f.readlines()
			for line in data:
				line = str(line).strip()
				dots = "."*(35-len(line))
				if dots == "": dots = " "
				go = 1
				counter = counter+1
				if line == "None": line = ""
				print("	("+f"{counter:03d}"+"/"+f"{substitutes:03d}"+") "+line,end="")
				line = line.replace("@"+kbinserver,"")
				try:
					driver.get("https://"+kbinserver+"/m/"+line)
					time.sleep(1)
					try: # checking for 404
						message = driver.find_element(By.XPATH, '//*[@id="content"]/p').text
						if "404" in message:
							print(dots+"not found (404).")
							go = 0
						else:
							go = 1
					except Exception as e:
						go = 1
					try:
						if go == 1:
							kbinBTN = driver.find_element(By.XPATH, '//*[@id="sidebar"]/section[1]/aside/form[1]/button')
							if kbinBTN.text == "Subscribe":
								kbinBTN.click()
								print(dots+"subscribed.")
								subscribed = subscribed+1
							elif kbinBTN.text == "Unsubscribe":
								print(dots+"already subsribed.")
								already = already+1
							elif "pending" in kbinBTN.text.lower():
								print(dots+"subscription pending.")
								pending = pending+1
							else:
								print(dots+"not subscribed (ERROR 1)")
								notsubbed = notsubbed+1
							go = 0
					except Exception as e2:
						if DEBUG == 1: print(dots+"not subscribed. "+str(e2)[0:50])
						else: print(dots+"not subscribed (ERROR 2)")
						notsubbed = notsubbed+1
				except Exception as e:
					print(dots+"not subscribed. Button not found")
					if DEBUG == 1: print(dots+str(e)[0:50])
					notsubbed = notsubbed+1
		os.remove("kbin.txt")
		return subscribed,already,notsubbed,pending
	except Exception as e:
		if DEBUG == 1 : print(dots+"ERROR 3"+str(e)[0:100])
		else: print(dots+"ERROR 3")
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

if DEBUG != 1:							# for progress display
	searchpercscale = len(subs)/100		
print("Looking for corresponding kbin magazines and lemmy communities.")
for sub in subs:
	counter = counter+1				# for progress display
	if DEBUG != 1:
		searchpercent = round(counter/searchpercscale,2)
		print ("	"+f"{counter:03d}"+"/"+f"{len(subs):03d}"+" subreddits searched ("+str(searchpercent)+"% completed)",end="\r")
	sub = str(sub)
	dots = "."*(34-len(sub))
	if dots == "": dots = " "
	if DEBUG == 1 : print("	("+f"{counter:03d}"+"/"+f"{len(subs):03d}"+") "+sub,end="")
	
	try: rehabresult,rehabresultname = subrehabsearch(sub)
	except: rehabresult,rehabresultname = 0,""
	try: kbinresult,kbinresultname = kbinsubsearch(sub)
	except: kbinresult,kbinresultname = 0,""
	try: lemmyresult,lemmyresultname = lemmysubsearch(sub)
	except: lemmyresult,lemmyresultname = 0,""
	
	#print("\nrehab:		",rehabresult,rehabresultname,"\nkbin.social:	",kbinresult,kbinresultname,"\nlemmy search:	",lemmyresult,lemmyresultname)
	
	resultlist = []
	if rehabresult == 1: resultlist.append(rehabresultname.lower())
	if kbinresult == 1: resultlist.append(kbinresultname.lower())
	if lemmyresult == 1: resultlist.append(lemmyresultname.lower())
	resultlist = list(set(resultlist)) # should delete duplicates
	
	file_object = open('kbin.txt', 'a')
	
	if len(resultlist)>0: file_object.write(resultlist[0]+"\n")
	if len(resultlist)>1: file_object.write(resultlist[1]+"\n")
	if len(resultlist)>2: file_object.write(resultlist[2]+"\n")
	if len(resultlist)>3: file_object.write(resultlist[3]+"\n")
	file_object.close()

	if DEBUG == 1: 
		if rehabresult+kbinresult+lemmyresult == 0: print(dots+"not found.")
		else:
			print(dots+"found "+str(' & '.join(resultlist))+".")
			substitutes_found = substitutes_found+1

if DEBUG == 1: print("Cleaning up duplicates")
else: print("\nCleaning up duplicates")
substitutes = cleankbin()
print("	Found "+str(substitutes)+" substitutes for "+str(len(subs))+" subreddits.")

print("Joining kbin communities")
subscribed,already,notsubbed,pending = kbinjoin(substitutes)

driver.quit()
print("\nProcess finished.\n	")
print("Subreddits pulled from Reddit:		",len(subs))
print("Substitutes found on Kbin & Lemmy:	",substitutes)
print("Subscribed on Kbin & Lemmy:		",subscribed)
print("Already subscribed:			",already)
print("Subscription pending:			",pending)
print("Not subscribed (Errors):		",notsubbed)
exit()