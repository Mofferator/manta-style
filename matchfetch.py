import urllib3, json, gspread, sys, requests, os
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv('.env')
KEY = os.getenv("OPENDOTAKEY")
BEARERTOKEN = os.getenv("STRATZTOKEN")

requests.packages.urllib3.disable_warnings()


# A match is a list of [MATCHID, TEAM(lost), TEAM(won)]
# A team is a list of 5 players
# A player is a list of [NAME, WIN?, STEAMID]

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
client = gspread.authorize(creds)


sheet = client.open("Balancer Bot Test Spreadsheet").worksheet("Sheet2")
if __name__ == "__main__":
    print("\nfetching player records...\n")
global playerrecords
playerrecords = sheet.get_all_records()
if __name__ == "__main__":
    print("fetch complete\n")

http = urllib3.PoolManager()

# Takes a spreadsheet and outputs a list of players [ID, MMR, NAME, SUPPORT?, STEAMID, wins/losses]
def ingestrecords():
    c = 2
    playerlist = []
    for ele in playerrecords:
        player = []
        player.append(c)
        player.append(ele["mmr"])
        player.append(ele["Name"])
        if ele["support?"] == "Yes":
            player.append(1)
        else:
            player.append(0)
        player.append(ele["id"])
        player.append(ele["real mmr"])
        player.append(ele["mmr override"])
        c += 1
        playerlist.append(player)
    return playerlist

# creates a dictionary of player steamids and row numbers
# e.g. {12345678 : 2}
playerlist = ingestrecords()
playerdictionary = {}
for player in playerlist:
    playerdictionary[player[4]] = player[0]

# Makes json look not cancer
def jsonprint(j):
    print(json.dumps(j, indent=4, sort_keys=True))


# converts a match into readable match data: list of [NAME, WIN?, STEAMID]
def getmatchdata(match):
    playerinfo = []
    print(match)
    playerinfo.append(match["id"])
    for x in match["players"]:
        player = []
        player.append(x["steamAccount"]["name"])
        player.append(x["isVictory"])
        player.append(x["steamAccount"]["steamId"])
        playerinfo.append(player)
    return playerinfo


# returns a list of match data
def getmatchidlist(leagueid):
    if __name__ == "__main__":
        print("fetching match records...\n")
    #ml = http.request("GET", "https://api.stratz.com/api/v1/league/" + leagueid + "/matches?include=Player&take=250")
    resp = http.request(
    "GET",
    "https://api.stratz.com/api/v1/league/11982/matches?include=Player&take=250",
    headers={
        "Authorization": "Bearer {}".format(BEARERTOKEN)
    }
    )
    playersetlist = []
    matchlist = json.loads(resp.data)
    if __name__ == "__main__":
        print("fetch complete")
    for match in matchlist:
        playersetlist.append(getmatchdata(match))
    return playersetlist

def getplayermmr(playerid):
    pid = playerdictionary[playerid]
    player = playerlist[pid - 2]
    if player[6] != "":
        mmr = int((int(player[6]) - 500)/67)
    else:
        p = http.request("GET", "https://api.opendota.com/api/players/" + str(playerid) + "?key=" + KEY)
        player = json.loads(p.data)
        mmr = player["rank_tier"]
        if mmr is None:
            return 3500
    print(mmr)
    realmmr = mmr * 67
    startingmmr = 4000 + ((realmmr - 4500) * 0.4)
    return startingmmr


# finds the first empty column to write to
def findlastcolum(sheet):
    last = 6
    for player in sheet:
        if len(player) > last:
            last = len(player)
    return last + 1


# converts column numbers to strings in A1 notation
# e.g. numtoA1(26) = "z"
# e.g. numtoA1(27) = "aa"
# up to a max of "zz"
def numtoA1(n):
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string







# creates a vertical buffer of empty cells to write to
def genemptycolumnofcells(column, length):
    columna1 = numtoA1(column)
    print(columna1)
    columna1.capitalize()
    ecoc = sheet.range("{}{}:{}{}".format(columna1.capitalize(), 1, columna1.capitalize(), length+10))
    return ecoc


# creates a horizontal buffer of empty cells to write to
def genemptyrowofcells(column1, column2, row):
    column1a1 = numtoA1(column1)
    column2a1 = numtoA1(column2)
    eroc = sheet.range("{}{}:{}{}".format(column1a1.capitalize(), row, column2a1.capitalize(), row))
    return eroc


# adds a player to the spreadsheet, the playerlist and the playerdictionary
def addplayer(name, steamid, row):
    cellrange = genemptyrowofcells(1, 6, row)
    playercelllist = cellrange
    player = [row, 4000, name, 0, steamid, 4000, ""]
    playerlist.append(player)
    playerdictionary[player[4]] = player[0]
    playercelllist[0].value = player[2]
    playercelllist[1].value = player[1]
    playercelllist[2].value = 4000
    playercelllist[3].value = 0
    playercelllist[4].value = player[4]
    playercelllist[5].value = ""
    sheet.update_cells(playercelllist)


# updates the spreadsheet given a list of matchids
def updatespreadsheet(matchlist):
    currentmatchlist = sheet.row_values(1)[6:int(len(sheet.row_values(1)))]
    def findnotrecorded(ml, cml):
        notrecorded = []
        for m in ml:
            if str(m[0]) not in cml:
                notrecorded.append(m)
        return notrecorded
    tobeadded = findnotrecorded(matchlist, currentmatchlist)
    tobeadded.reverse()
    lastcolum = findlastcolum(playerrecords)
    lastrow = len(playerrecords) + 2
    for match in tobeadded:
        cell_buffer = genemptycolumnofcells(lastcolum, lastrow)
        cell_buffer[0].value = match[0]
        for player in match[1:11]:
            if player[2] not in playerdictionary:
                addplayer(player[0], player[2], lastrow)
                lastrow += 1
                print("player: {} added".format(player[0]))
            if player[1] is True:
                cell_buffer[playerdictionary[player[2]]-1].value = "W"
            else:
                cell_buffer[playerdictionary[player[2]]-1].value = "L"
        lastcolum += 1
        sheet.update_cells(cell_buffer)
        print("match: {} added\n".format(match[0]))



def updatemmr():
    global playerrecords
    playerrecords = sheet.get_all_records()
    currentmatchlist = sheet.row_values(1)[6:int(len(sheet.row_values(1)))]
    winlosslist =[]
    for player in playerlist:
        player[5] = getplayermmr(player[4])
        player[1] = 4000
    for match in currentmatchlist:
        winners = []
        losers = []
        for player in playerrecords:
            if player[match] == "W":
                winners.append(playerlist[playerdictionary[player["id"]]-2])
            elif player[match] == "L":
                losers.append(playerlist[playerdictionary[player["id"]]-2])
        winlosslist.append([winners, losers])
    for match in winlosslist:
        def teameloavg(team):
            total = 0
            for player in team:
                total += playerlist[player[0] - 2][5]
            return total/5
        winnermmr = teameloavg(match[0])
        losermmr = teameloavg(match[1])
        mmrchange = 400 * (1 - (1/(1 + pow(10, ((losermmr - winnermmr)/4000)))))
        print(mmrchange)
        for player in match[0]:
            playerlist[player[0] - 2][1] += mmrchange
            playerlist[player[0] - 2][5] += mmrchange/5
        for player in match[1]:
            playerlist[player[0] - 2][1] -= mmrchange
            playerlist[player[0] - 2][5] -= mmrchange/5
    mmrlist = sheet.range("B2:B{}".format(len(playerlist)+1))
    realmmrlist = sheet.range("C2:C{}".format(len(playerlist)+1))
    i = 0
    for cell in mmrlist:
        cell.value = round(playerlist[i][1])
        i = i + 1
    i = 0
    for cell in realmmrlist:
        cell.value = round(playerlist[i][5])
        i = i + 1
    sheet.update_cells(mmrlist)
    sheet.update_cells(realmmrlist)


def updateleague(leagueid):
    midl = getmatchidlist(str(leagueid))
    print("\nupdating spreadsheet...\n")
    updatespreadsheet(midl)
    print("spreadsheet updated")
    updatemmr()

if __name__ == "__main__":
    leagueid = 11982
    updateleague(leagueid)


# print(playerrecords)


