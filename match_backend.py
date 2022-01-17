from matchfetch import getmatchdata, getmatchidlist, jsonprint
import requests
import json
from json import JSONEncoder
import urllib3
import os
from MatchStats import MatchStats
import ingestionengine as ing
from dotenv import load_dotenv

load_dotenv('.ENV')
apikey = os.getenv("OPENDOTAKEY")


import gspread
from oauth2client.service_account import ServiceAccountCredentials
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Balancer Bot Test Spreadsheet").worksheet("Sheet2")
sheetrecords = sheet.get_all_records()
def ingestrecords():
    from player import player
    c = 2
    playerlist = []
    for ele in sheetrecords:
        p = player(c, ele["mmr"], ele["real mmr"], ele["Name"], ele["support?"], ele["id"])
        playerlist.append(p)
        c += 1
    return playerlist



http = urllib3.PoolManager()
apikey = "9abe4726-eb62-43e7-aab7-18588fac3f05"

with open("heroes.json") as json_file:
	heroes = json.load(json_file)
def heroidtoname(hid):
	for hero in heroes["heroes"]:
		if hero["id"] == hid:
			return [hero["localized_name"], hero["name"]]

class PlayerStats():
	def __init__(self, name, steamid, hero, heroname, kills, deaths, assists, hDMG):
		self.name = name
		self.sid = steamid
		self.h = hero
		self.hn = heroname
		self.k = kills
		self.d = deaths
		self.a = assists
		self.dmg = hDMG

def playerstatsprint(player):
	print("\tName: {}".format(player.name))
	print("\tSteam ID: {}".format(player.sid))
	print("\tHero ID: {}".format(player.h))
	print("\tKills: {}".format(player.k))
	print("\tDeaths: {}".format(player.d))
	print("\tAssists: {}".format(player.a))
	print("\tHero Damage: {} \n".format(player.dmg))


def getlistofids(leagueid):
	idlist = []
	gamelist = getmatchidlist(str(leagueid))
	for game in gamelist:
		idlist.append(game[0])
	return idlist


class MatchEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__

def getmatchstats(matchid):
	print("Getting {}...".format(matchid))
	m = http.request("GET", "https://api.opendota.com/api/matches/" 
					 + str(matchid)
					 + "?api_key="
					 + apikey)
	match = json.loads(m.data)
	playerlist = []
	for player in match["players"]:
		p = PlayerStats(player["personaname"],
						player["account_id"],
						heroidtoname(player["hero_id"])[0],
						heroidtoname(player["hero_id"])[1],
						player["kills"],
						player["deaths"],
						player["assists"],
						player["hero_damage"])
		playerlist.append(p)
	def getwinner(match):
		if match["players"][0]["win"] == 1:
			return 0
		else:
			return 1


	return MatchStats(matchid,
					  getwinner(match),
					  match["radiant_score"],
					  match["dire_score"],
					  match["duration"],
					  playerlist,
					  match["start_time"])

def getleaguestats(listofids):
	listofmatches = []
	for id in listofids:
		listofmatches.append(getmatchstats(id))
	return listofmatches


def matchstatsprint(match):
	print("Match ID: {}".format(match.id))
	print("Winner: {}".format(match.w))
	print("Radiant score: {}".format(match.rs))
	print("Dire score: {}".format(match.ds))
	print("Duration(s): {}".format(match.dur))
	for player in match.p:
		playerstatsprint(player)

def reingestmatch(mj):
	playerlist = []
	for player in mj["p"]:
		p = PlayerStats(player["name"], 
					player["sid"],
					player["h"],
					player["hn"],
					player["k"],
					player["d"],
					player["a"],
					player["dmg"])
		playerlist.append(p)
	return MatchStats(mj["id"],
					  mj["w"],
					  mj["rs"],
					  mj["ds"],
					  mj["dur"],
					  playerlist,
					  mj["t"])


def reingestleague(lj):
	matchlist = []
	for match in lj:
		matchlist.append(reingestmatch(match))
	return matchlist


def writejsontofile(jsondata):
	with open("matchdata.txt", "w") as outfile:
		json.dump(jsondata, outfile)

def readjsontoclasslist():
	if os.stat("matchdata.txt").st_size != 0:
		with open("matchdata.txt") as json_file:
			leaguedata = json.load(json_file)
			return reingestleague(leaguedata)
	else:
		return []

def pulldownrecords(leagueid):
	currentidlist = []
	def pull(leagueid):
		print("pulling match records...")
		leaguestats = getleaguestats(getlistofids(leagueid))
		leagueJSONData = json.dumps(leaguestats, indent=4, cls=MatchEncoder)
		leagueJSON = json.loads(leagueJSONData)
		writejsontofile(leagueJSON)
	if os.stat("matchdata.txt").st_size != 0:
		with open("matchdata.txt") as json_file:
			leaguedata = json.load(json_file)
			for match in leaguedata:
				currentidlist.append(match["id"])
		if currentidlist != getlistofids(11982):
			pull(leagueid)
	else:
		pull(leagueid)

def requestmatch(matchid):
	with open("matchdata.txt") as json_file:
		leaguedata = json.load(json_file)
		for match in leaguedata:
			if match["id"] == matchid:
				return reingestmatch(match)
playerlist = ingestrecords()
playerdictionary = {}
for player in playerlist:
    playerdictionary[player.steamid] = player.playerid

def listmatchesplayedin(steamid):
	playerid = playerdictionary[steamid]
	playerrow = sheetrecords[playerid-2]
	matchplayedlist = []
	for mID, result in playerrow.items():
		if result == "L" or result == "W":
			match = requestmatch(int(mID))
			for player in match.p:
				if player.sid == steamid:
					matchplayedlist.append([mID, result, player])

	return matchplayedlist



if __name__ == "__main__":
	pulldownrecords(11982)
	#print(listmatchesplayedin(108305168))
	
	for match in readjsontoclasslist():
		#matchstatsprint(match)
		pass
