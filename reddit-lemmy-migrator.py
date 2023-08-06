"""
Reddit to Lemmy migration assistant		v.1.5 (20230804)
	New changes:
	-sub.rehab implementation
		additionally to old method, also searches sub.rehab for subreddit substitute
	-sizeable UX overhaul
		-progress display for community search (disabled in DEBUG mode)
		-simplified output in normal and DEBUG mode
		-added spacing dots to make list outputs more cohesive
		-added custom messaging for common errors

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
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from getpass import getpass
import os

# VARIABLES ------------------------------------------------------------------------------
reddURL = "https://old.reddit.com/subreddits/"
reddcredstatus = "not set"
lemmyserverstatus = "not set"
lemmycredstatus = "not set"
ARGLOGIN = 0

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
try:
	chromedriver_autoinstaller.install()
	chrome_options = Options()
	chrome_options.add_argument("--disable-extensions")
	chrome_options.add_argument("--disable-gpu")
	if DEBUG != 1: chrome_options.add_argument("--headless")
	driver = webdriver.Chrome(options=chrome_options)
except Exception as e:
	print("Error while setting up chromedriver")
	if DEBUG == 1: print(e)
	exit()
	
# GET LOGIN DATA -------------------------------------------------------------------------
def getredditlogin():
	redduname = input("Reddit username:	")
	reddpass = getpass("Reddit password:	")
	return redduname, reddpass

def getlemmyserver():
	lemmserver = input("Lemmy instance:		")
	return lemmserver
	
def getlemmylogin():
	lemmuname = input("Lemmy username:		")
	lemmpass = getpass("Lemmy password:		")
	return lemmuname,lemmpass

def checkreddlogin(redduname,reddpass):
	if DEBUG == 1 : print("	Reddit login data is being checked")
	try:
		driver.get(reddURL)
		driver.find_element(By.XPATH, '//*[@id="login_login-main"]/input[2]').send_keys(redduname)
		driver.find_element("id", "rem-login-main").click()
		driver.find_element(By.XPATH, '//*[@id="login_login-main"]/input[3]').send_keys(reddpass)
		driver.find_element(By.XPATH, '//*[@id="login_login-main"]/div[4]/button').click()
		time.sleep(3)
		try:
			loginstatus = driver.find_element(By.XPATH,'//*[@id="login_login-main"]/div[2]').text
			if DEBUG == 1 and loginstatus != "incorrect username or password": print("	Reddit login status"+loginstatus)
			print("	Reddit login data incorrect")
			return "false_login"
		except NoSuchElementException:
			print("	Reddit login success")
			return "OK"
		except Exception as e2:
			if DEBUG == 1 : print("	Reddit login verification error:\n		"+str(e2)[0:320])
	except Exception as e:
		if DEBUG == 1 : print("	Reddit login verification error:\n		"+str(e)[0:320])
		else: print(" Reddit login could not be verified due to an error.")
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
		driver.find_element(By.XPATH, '//*[@id="app"]/div[2]/div/div/div/div/div/form/div[2]/div/div/div/input').send_keys(lemmpass)
		driver.find_element(By.XPATH, '//*[@id="app"]/div[2]/div/div/div/div/div/form/div[2]/div/div/div/input').send_keys(Keys.ENTER)
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
		if DEBUG == 1 : print(str(e)[0:320])
		exit()
	try:
		subs = multi.replace("https://old.reddit.com/r/","").split("+")
		print("	Found",len(subs),"subreddits")
		return subs
	except Exception as e:
		print("	Error processing subreddit list")
		if DEBUG == 1 : print("	",str(e)[0:320])
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

def lemmysubsearch(lemmserver,sub):
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
		return 1,topresult
	except NoSuchElementException:
		return 0,""
	except Exception as e:
		if DEBUG == 1 :
			try: print(" and produced an error: "+str(''.join(re.findall("(.*)",e)[:1])))
			except: print(" and produced an error: ",e)
		return 0,""

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
		os.rename("lemmy2.txt","lemmy.txt")
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
					dots = "."*(45-len(line))
					try:
						driver.get("https://"+lemmserver+"/c/"+line)
						time.sleep(1)
						try:
							LemmyBTN = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-secondary.d-block.mb-2.w-100").text
							resolved = 0
						except:
							# Button not found. Either 'Subscribe pending' or other issue.
							# Checking for subscribe pending
							try:
								print(dots+"not subscribed (1) "+driver.find_element(By.XPATH,'//*[@id="sidebarMain"]/div/button').text+".")
								resolved = 1
							except Exception as e3:
								resolved = 0
							# Checking for Error with message 
							if resolved == 0:
								try:
									message = driver.find_element(By.XPATH,'//*[@id="app"]/div[2]/div/p').text
									if "Try refreshing" in message:
										print("."*(37-len(line))+"retrying.....",end="")
										dots = ""
										driver.get("https://"+lemmserver+"/c/"+line)
										time.sleep(30)
										LemmyBTN = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-secondary.d-block.mb-2.w-100").text
									else: LemmyBTN = message							
								except Exception as e4:
									LemmyBTN = str(e4)[0:100]
									if "Unable to locate element" in LemmyBTN: LemmyBTN = "Subscribe button not found (1)."
						if resolved == 0 and LemmyBTN == "Subscribe":
							driver.find_element(By.CSS_SELECTOR, "button.btn.btn-secondary.d-block.mb-2.w-100").click()
							print(dots+"subscribed.")
						elif resolved == 0 and LemmyBTN == "Joined":
							print(dots+"already subsribed.")
						elif resolved == 0:	
							if len(LemmyBTN)>50: print(dots+"not subscribed (2) "+LemmyBTN[0:50]+"...")
							else: print(dots+"not subscribed (3) "+LemmyBTN)
						resolved = 1
					except Exception as e2:
						if "Unable to locate element" in str(e2):
							try:
								print(dots+"not subscribed (4) "+driver.find_element(By.XPATH,'//*[@id="sidebarMain"]/div/button').text+".")
							except Exception as e3:
								print(dots+"not subscribed. Subscribe button not found (2).")
								if DEBUG == 1: print("		",str(e3)[0:100])
						elif DEBUG == 1:
							try: print(dots+"not subscribed (5) ",str(e2)[0:100])
							except: print(dots+"not subscribed (6) ",e2)
						else: print(dots+"not subscribed (7)")
		os.remove("lemmy.txt") 
	except Exception as e:
		print("	Error while joining Lemmy communities.")
		if DEBUG == 1 :
			try: print(''.join(re.findall("(.*)",e)[:1]))
			except:
				try: print(str(e)[0:320])
				except: print(e)
		exit()

# EXECUTION ------------------------------------------------------------------------------
print("Welcome to the Reddit to Lemmy migration tool.\n")
print("It will create a list of your subscribed subreddits, look for communities with the same name on Lemmy")
print("and subscribe to the community with the most subscribers (searching through lemmy.world)\n")

if ARGLOGIN == 1:
	if DEBUG == 1: print("Login data received from command line arguments")
	reddcredstatus = checkreddlogin(redduname,reddpass)
	if DEBUG == 1 and reddcredstatus != "OK": print("		Reddit credentials in command line arguments seem to be incorrect")
	lemmyserverstatus = checklemmyserver(lemmserver)
	if DEBUG == 1 and lemmyserverstatus != "OK": print("		Lemmy instance in command line arguments seems to be incorrect")
	lemmycredstatus = checklemmylogin(lemmserver,lemmuname,lemmpass)
	if DEBUG == 1 and lemmycredstatus != "OK": print("		Lemmy credentials in command line arguments seem to be incorrect")
else: print("Please enter your Reddit account info")

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

if DEBUG != 1:							# for progress display
	searchpercscale = len(subs)/100		
	searchpercent = 0
	counter = 0
print("Looking for corresponding communities on Lemmy.")
for sub in subs:
	if DEBUG != 1:						# for progress display
		counter = counter+1
		searchpercent = round(counter/searchpercscale,2)
		print ("	",counter,"/",len(subs)," subreddits searched (",searchpercent,"% completed )",end="\r")
	sub = str(sub)
	if DEBUG == 1 : print("	r/"+sub,end="")
	dots = "."*(43-len(sub))
#	Sub.Rehab search
	try:
		rehabresult,rehabresultname = subrehabsearch(sub)
	except Exception as e:
		rehabresult = 0
		if DEBUG == 1: print(e)
#	Lemmy search (old method)
	try:
		lemmyresult,lemmyresultname = lemmysubsearch(lemmserver,sub)
		if lemmyresultname == str and lemmyresultname.startswith("@") == True: lemmyresultname = sub+lemmyresultname
	except:
		lemmyresultname = ""
		lemmyresult = 0

	file_object = open("lemmy.txt", "a")
	#print("\nrehab:	",rehabresultname,"\nlemmy:	",lemmyresultname,"\n")
	if lemmyresultname == rehabresultname: file_object.write(lemmyresultname+"\n")
	else: file_object.write(rehabresultname+"\n"+lemmyresultname+"\n")
	file_object.close()

	try:
		if DEBUG == 1:
			if lemmyresult+rehabresult == 0: print(dots+"not found.")
			else: print(dots+"found: ",end="")
			if lemmyresult+rehabresult == 1:
				if rehabresult == 1: print(rehabresultname)
				if lemmyresult == 1: print(lemmyresultname)
			if lemmyresult+rehabresult == 2:
				if lemmyresultname == rehabresultname: print(rehabresultname,"(x2)")
				else: print(rehabresultname,"&",lemmyresultname+".")
			elif DEBUG != 1 : print(dots+"ERROR while searching on Lemmy.")
	except Exception as e:
		if DEBUG == 1:
			try: print(dots+"EXCEPTION: "+str(''.join(re.findall("(.*)",e)[:1])))
			except: print(dots+"EXCEPTION: ",e)
		else: print(dots+"EXCEPTION.")

if DEBUG == 1 : print("Cleaning up result list")
lemmycleanup()

print("Joining Lemmy communities")
lemmyjoin()

driver.quit()
print("\nProcess finished.")