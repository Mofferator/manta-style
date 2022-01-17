from flask import Flask, render_template, url_for, redirect, request
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime as dt
import datetime, gspread, cmdlineversion, teamgeneration, match_backend, json, urllib3, os
import ingestionengine as ing
from player import player
from match_backend import pulldownrecords
from dotenv import load_dotenv


load_dotenv('.ENV')
apikey = os.getenv("OPENDOTAKEY")
BEARERTOKEN = os.getenv("STRATZTOKEN")

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
client = gspread.authorize(creds)

http = urllib3.PoolManager()
sheet = client.open("Balancer Bot Test Spreadsheet").worksheet("Sheet2")
playerrecords = sheet.get_all_records()

class player:
    def __init__(self, playerid, realmmr, mmr, name, support, steamid):
        self.playerid=playerid
        self.mmr = mmr
        self.realmmr = realmmr
        self.name = name
        self.support = support
        self.steamid = steamid




# returns the mmr from a player
def getmmr(player):
	return player.mmr

def sortmp(playerlist):
	pil = []
	for player in playerlist:
		playeritem = []
		playeritem.append(player)
		playeritem.append(len(match_backend.listmatchesplayedin(player.steamid)))
		pil.append(playeritem)
	def getmp(playeritem):
		return playeritem[1]
	pil.sort(key=getmp, reverse=True)
	playerlist2 = []
	for playeritem in pil:
		playerlist2.append(playeritem[0])
	return playerlist2


app = Flask(__name__)


@app.route("/")
@app.route("/home")
@app.route("/matchlist")
def home():
	match_backend.pulldownrecords(11982)
	matchlist = match_backend.readjsontoclasslist()
	listofmatchdata = []
	for match in matchlist:
		newmatch = []
		newmatch.append(str(match.id))
		newmatch.append(str(dt.fromtimestamp(match.t)))
		newmatch.append(str(datetime.timedelta(seconds=match.dur)))
		listofmatchdata.append(newmatch)

	return render_template("hello.html", ml=listofmatchdata)

@app.route("/playerlist", methods=["GET"])
def playerlist():
	client.login()
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

	pulldownrecords(11982)
	playerlist = ingestrecords()
	playerdictionary = {}
	for player in playerlist:
		playerdictionary[player.steamid] = player.playerid
	playerlist.sort(key=getmmr, reverse=True)
	pil = []
	for player in playerlist:
		playeritem = []
		playeritem.append(player)
		playeritem.append(len(match_backend.listmatchesplayedin(player.steamid)))
		a = http.request("GET", "https://api.opendota.com/api/players/"
							+ str(player.steamid)
							+ "?api_key=" + apikey)
		avatar = json.loads(a.data)["profile"]["avatarfull"]

		playeritem.append(avatar)
		pil.append(playeritem)

	return render_template("playerlist.html",
						   playeritemlist=pil)

@app.route("/balancer", methods=["GET", "POST"])
def balancer():
	client.login()
	sheet = client.open("Balancer Bot Test Spreadsheet").worksheet("Sheet2")
	sheetrecords = sheet.get_all_records()
	pulldownrecords(11982)

	def ingestrecords():
		from player import player
		c = 2
		playerlist = []
		for ele in sheetrecords:
			p = player(c, ele["mmr"], ele["real mmr"], ele["Name"], ele["support?"], ele["id"])
			playerlist.append(p)
			c += 1
		return playerlist


	playerlist = sortmp(ingestrecords())
	playerdictionary = {}
	for player in playerlist:
		playerdictionary[player.steamid] = player.playerid
	return render_template("balancer.html", playerlist=playerlist, missing=10)

@app.route("/handle_data", methods=["POST"])
def handle_data():
	client.login()
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
	playerlist = sortmp(ingestrecords())
	playerdictionary = {}
	for player in playerlist:
		playerdictionary[player.steamid] = player.playerid
	selectedplayers = request.form.getlist('check')
	supportlist = request.form.getlist("support")
	selectedsupports = []
	for id in supportlist:
		if id in selectedplayers:
			selectedsupports.append(id)
	if len(selectedplayers) != 10:
		return render_template("balancer.html",
							   missing=10-len(selectedplayers),
							   playerlist=playerlist,
							   alreadyselected=selectedplayers)
	elif len(selectedsupports) != 4:
		playerlist = sortmp(ingestrecords())
		if len(selectedsupports) > 4:
			missingmsg = "Please select {} fewer supports".format(len(selectedsupports) - 4)
		if len(selectedsupports) < 4:
			missingmsg = "Please select {} more supports".format(4 - len(selectedsupports))
		return render_template("balancer.html",
							   missing=0,
							   playerlist=playerlist,
							   alreadyselected=selectedplayers,
							   alreadyselectedsupports=selectedsupports,
							   missingmsg=missingmsg)
	else:
		pool = cmdlineversion.IdListToPool(selectedplayers)
		for id in selectedsupports:
			for player in pool:
				if player.playerid == int(id):
					player.support = 1
		selectedcores = []
		for id in selectedplayers:
			if id not in selectedsupports:
				selectedcores.append(id)
		for id in selectedcores:
			for player in pool:
				if player.playerid == int(id):
					player.support = 0
		listofmatchunparsed = cmdlineversion.getsuppmatchlist(pool)
		listofmatchparsed = []
		for match in listofmatchunparsed:
			team1 = []
			team2 = []
			for player in match[0]:
				team1.append([player.name, player.support])
			for player in match[1]:
				team2.append([player.name, player.support])
			match = [team1, team2, cmdlineversion.calcmmravg(match[0]), cmdlineversion.calcmmravg(match[1])]
			listofmatchparsed.append(match)
			firstmatch = []
			firstmatch.append(listofmatchparsed[0])
		return render_template("handle_data.html", matchlist=firstmatch)

@app.route("/spreadsheet")
def spreadsheet():
	return render_template("spreadsheet.html")

@app.route("/match/<int:matchid>")
def match(matchid):
	match_backend.pulldownrecords(11982)
	match = match_backend.requestmatch(matchid)
	team1 = match.p[0:5]
	team2 = match.p[5:10]
	return render_template("matchpage.html",
						   team1=team1,
						   team2=team2,
						   winner=match.w,
						   duration=str(datetime.timedelta(seconds=match.dur)),
						   rscore=match.rs,
						   dscore=match.ds,
						   time=dt.fromtimestamp(match.t))


@app.route("/player/<int:steamid>")
def player(steamid):
	client.login()
	sheet = client.open("Balancer Bot Test Spreadsheet").worksheet("Sheet2")
	sheetrecords = sheet.get_all_records()
	pulldownrecords(11982)

	def ingestrecords():
		from player import player
		c = 2
		playerlist = []
		for ele in sheetrecords:
			p = player(c, ele["mmr"], ele["real mmr"], ele["Name"], ele["support?"], ele["id"])
			playerlist.append(p)
			c += 1
		return playerlist
	playerlist = ingestrecords()
	def requestplayer(steamid):
		for player in playerlist:
			if player.steamid == steamid:
				return player
	player = requestplayer(steamid)
	name = player.name
	playerdictionary = {}
	for player in playerlist:
		playerdictionary[player.steamid] = player.playerid
	matchlist = match_backend.listmatchesplayedin(steamid)

	a = http.request("GET", "https://api.opendota.com/api/players/"
							+ str(steamid)
							+ "?api_key=" + apikey)
	avatar = json.loads(a.data)["profile"]["avatarfull"]
	wins = 0
	losses = 0
	for game in matchlist:

		if game[1] == "W":
			wins += 1
		else:
			losses += 1
	record = [wins, losses]

	return render_template("player.html", name=name,
										  ml = matchlist,
										  avatarlink = avatar,
										  record = record)

if __name__ == "__main__":
	app.run(debug=True)