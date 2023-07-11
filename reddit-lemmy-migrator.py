# Reddit to Lemmy migration assistant
#	v.1.0 (20230711)
#
# 	github.com/induna-crewneck/
# This script is meant to automate migration from Reddit to Lemmy by getting a list of 
#	your subscribed subreddits, looking for them on Lemmy and subscribing to them there.
# python3

DEBUG = 0

# IMPORTS --------------------------------------------------------------------------------
from bs4 import BeautifulSoup 
import requests
import re
import time
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import os

# VARIABLES ------------------------------------------------------------------------------
reddURL = "https://old.reddit.com/subreddits/"
reddcredstatus = "not set"
lemmyserverstatus = "not set"
lemmycredstatus = "not set"

# PRE-SETUP ------------------------------------------------------------------------------
chrome_options = Options()
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--headless")
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
	print("	Reddit login data",end="")
	try:
		driver.get(reddURL)
		driver.find_element(By.XPATH, '//*[@id="login_login-main"]/input[2]').send_keys(redduname)
		driver.find_element("id", "rem-login-main").click()
		driver.find_element(By.XPATH, '//*[@id="login_login-main"]/input[3]').send_keys(reddpass)
		driver.find_element(By.XPATH, '//*[@id="login_login-main"]/div[4]/button').click()
		#driver.find_element(By.XPATH, '//*[@id="login_login-main"]/input[3]').send_keys(Keys.ENTER)
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
		print("	Error obtaining subreddit list")
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

def lemmysubcheck(sub):
	s = requests.session()
	response = s.get("https://lemmy.world/c/"+sub)
	responsecode = int(str(re.findall(r"\d{3}", str(response)))[2:5])
	if responsecode == 200:
		file_object = open('lemmy.txt', 'a')
		file_object.write("\n"+sub+"@lemmy.world")
		file_object.close()
		return 1

def lemmysubsearch(sub):
	try:
		lemmysearchURL = "https://lemmy.world/search?q="+sub+"&type=Communities&sort=TopAll"
		driver.get(lemmysearchURL)
		searchresult = driver.page_source.encode("utf-8")
		try:
			topresult = re.search("!"+sub+"@([^\s]+)", str(searchresult))
			sub_string = topresult.group()
		except:
			# Nothing on other instances
			return
		topresult = sub_string.replace('"','').replace('!','')
		file_object = open("lemmy.txt", "a")
		topresult = str(topresult)
		file_object.write("\n"+topresult)
		file_object.close()
		try:
			topinstance = topresult.replace(sub+"@","")
			return topinstance
		except:
			return topresult
	except Exception as e:
		if DEBUG == 1 : print("lemmysubcheck ERROR: ",e)

def lemmycleanup():
	try:
		with open("lemmy.txt","r") as f:
			data = f.readlines()
			for line in data:
				f2 = str(line)
				f3 = re.search("^[^\(]+", f2)
				f4 = f3.group()
				f5 = re.sub("]","",f4).strip()
				file_object = open("lemmy2.txt", "a")
				file_object.write("\n"+f5)
				file_object.close()
	except Exception as e:
		print(" Error while processing lemmy community list.")
		if DEBUG == 1 : print(e)
		try: os.remove("lemmy2.txt")
		except: return
	os.remove("lemmy.txt")
	os.rename("lemmy2.txt","lemmy.txt")

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
						#if DEBUG == 1 : print(e2)
		os.remove("lemmy.txt")
	except Exception as e:
		print("	Error while joining Lemmy communities.")
		if DEBUG == 1 : print(e)
		exit()

# EXECUTION ------------------------------------------------------------------------------
print("Welcome to the Reddit to Lemmy migration tool.\n")
print("It will create a list of your subscribed subreddits, look for communities with the same name on Lemmy")
print("and subscribe to the community with the most subscribers. If there is a community on lemmy.world that is")
print("not the one with the most subscribers, it will still be subscribed to.\n")

print("Please enter your Reddit account info")

while reddcredstatus != "OK":
	redduname,reddpass = getredditlogin()
	reddcredstatus = checkreddlogin(redduname,reddpass)

print("\nPlease enter your Lemmy account info ('instance' is the server you signed-up on, like lemmy.world)")
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
		worldstatus = lemmysubcheck(sub)
		otherstatus = lemmysubsearch(sub)
		if DEBUG == 1:
			if worldstatus == 1:
				if otherstatus == None: print(" found on lemmy.world")
				else: print(" found on lemmy.world and "+otherstatus)
			elif otherstatus != None: print(" found on "+otherstatus)
			else: print(" not found on lemmy")
	except Exception as e3:
		if DEBUG == 1 : print("\n")
		print("Error looking for "+sub+": "+e3)

if DEBUG == 1 : print("	Cleaning up result list")
lemmycleanup()

print("\nJoining Lemmy communities")
lemmyjoin()

driver.quit()
print("\nProcess finished.")