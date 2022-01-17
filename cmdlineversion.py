import teamgeneration
import ingestionengine as ing
from player import player
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
client = gspread.authorize(creds)

sheet = client.open("Balancer Bot Test Spreadsheet").worksheet("Sheet2")
playerrecords = sheet.get_all_records()

"""
A player is a list of [ID, ELO, NAME, SUPPORT?]
A team is a list of 5 players
A playerpool is a list of 10 players
"""

player1 = player(1, 4000, 6500, "FooSquash", 0, 123456789)
player2 = [3, 4348, "Bonions", 0]
player3 = [4, 3806, "Senya", 0]
player4 = [5, 3928, "BowiE", 1]
player5 = [6, 3601, "Moff", 0]
player6 = [7, 4869, "Gene", 0]
player7 = [8, 4529, "Liver", 1]
player8 = [9, 3814, "BoopXy", 1]
player9 = [10, 3414, "CornDog", 0]
player10 = [11, 3614, "Beaver", 1]

playerpool1 = [player1, player2, player3, player4, player5, player6, player7, player8, player9, player10]

testteam1 = [player1, player5, player8, player9, player10]
testteam2 = [player2, player3, player4, player6, player7]

class player:
    def __init__(self, playerid, mmr, realmmr, name, support, steamid):
        self.playerid=playerid
        self.mmr = mmr
        self.realmmr = realmmr
        self.name = name
        self.support = support
        self.steamid = steamid

theplayerlist = ing.ingestrecords() 
# calculated the elo average of a team
def calcmmravg(team):
    total = 0
    for player in team:
        total += player.realmmr
    return total/5

def IdListToPool(idlist):
    playerlist = ing.ingestrecords()
    pool = []
    for id in idlist:
        pool.append(playerlist[int(id)-2])
    return pool


# checks if the pool contains enough supports for a valid game
def isvalidpool(pool):
    total = 0
    for player in pool:
        total += player.support
    if total == 4:
        return 1
    else:
        return 0


# checks if a set of 2 teams contains the correct amount of supports on each team
def isvalidteamset(teams):
    def checkteam(team):
        total = 0
        for player in team:
            total += player.support
        if total == 2:
            return True
        else:
            return False
    if checkteam(teams[0]) and checkteam(teams[1]):
        return 1
    else:
        return 0


# creates a list of all the teams and sorts them by mmr difference (lowest -> highest)
def findbestteams(teamlist):
    currentbest = 5000
    bestteams = []
    for teams in teamlist:
        diff = abs(calcmmravg(teams[0]) - calcmmravg(teams[1]))
        teams.append(diff)
        teams.append(isvalidteamset(teams))
        if diff < currentbest:
            bestteams.append(teams)
        if len(bestteams) > 100:
            bestteams.pop(99)

    def getdiff(team):
        return team[2]
    bestteams.sort(key=getdiff)
    return bestteams


# prints the list of team sorted by mmr difference in a readable manner
def printbestteamlist(pool):
    teamset = findbestteams(teamgeneration.genteamlist(pool))
    for team in teamset:
        print(team, "\n")


# produces the best possible match of the given pool, considers mmr difference and support distribution
def getbestmatchsupp(pool):
    teamset = findbestteams(teamgeneration.genteamlist(pool))
    for team in teamset:
        if team[3] == 1:
            return team

def getbestmatch(pool):
    teamset = findbestteams(teamgeneration.genteamlist(pool))
    return teamset[0]

def getsuppmatchlist(pool):
    teamset = findbestteams(teamgeneration.genteamlist(pool))
    validteamlist = []
    for team in teamset:
        if team[3] == 1:
            validteamlist.append(team)
    return validteamlist

# formats a matchup to be readable on the command line
def formatteams(teams):
    team1 = teams[0]
    team2 = teams[1]
    team1names = []
    team2names = []
    diff = teams[2]
    for player in team1:
        team1names.append(player.name)
    for player in team2:
        team2names.append(player.name)
    print("Team 1: {} | Average mmr: {}".format(team1names, calcmmravg(team1)))
    print("Team 2: {} | Average mmr: {}".format(team2names, calcmmravg(team2)))
    print("MMR Difference: {}".format(diff))


def listsupportids(pool):
    supports = []
    for player in pool:
        if player.support == 1:
            supports.append(player.playerid)
    return supports


def listcoreids(pool):
    cores = []
    print(pool)
    for player in pool:
        print(player.name)
        if player.support == 0:
            cores.append(player.playerid)
            print(player.playerid)
    return cores


def main():
    playerids = []
    while len(playerids) < 10:
        id = (input("input player id:   "))
        if id == "listids":
            ing.listids()

        elif \
                id.isnumeric() is False \
                or int(id) >= len(theplayerlist) + 2 \
                or int(id) <= 1 \
                or id in playerids:
            print("{} is an invalid id".format(id))
        elif id != "":
            print("\t{} added".format(theplayerlist[int(id)-2].name))
            playerids.append(id)

    playerpool = []
    for id in playerids:
        playerpool.append(theplayerlist[int(id)-2])
    if isvalidpool(playerpool):
        print("\npool ok")
        formatteams(getbestmatch(playerpool))
    else:
        def countsupports(playerpool):
            supportcount = 0
            for player in playerpool:
                if player.support == 1:
                    supportcount += 1
            return supportcount
        supps = countsupports(playerpool)
        print("There are {} supports and {} cores".format(supps, 10 - supps))
        switch = []
        listsupps = listsupportids(playerpool)
        def listsuppnames(supportpool):
            names = []
            for id in supportpool:
                names.append(theplayerlist[int(id)-2].name + "({})".format(id))
            return names
        listcores = listcoreids(playerpool)
        def listcorenames(corepool):
            names = []
            print(corepool)
            for id in corepool:
                names.append(theplayerlist[int(id)-2].name + "({})".format(id))
            return names
        if supps > 4:
            print("{} of {} switch to core".format(supps - 4, listsuppnames(listsupportids(playerpool))))
            while supps > 4:
                switcher = input("input ids of players who are switching:  ")
                if int(switcher) in listcores:
                    print("Player is already playing core")
                elif switcher in playerids:
                    switch.append(switcher)
                    supps -= 1
                else:
                    print("invalid id")
        elif supps < 4:
            print("{} of {} must switch to support".format(4 - supps, listcorenames(listcoreids(playerpool))))
            while supps < 4:
                switcher = input("input ids of players who are switching:  ")
                if int(switcher) in listsupps:
                    print("player is already supporting")
                elif switcher in playerids:
                    supps += 1
                    switch.append(switcher)
                else:
                    print("invalid id")
        for id in switch:
            if theplayerlist[int(id)-2].support == 1:
                theplayerlist[int(id)-2].support = 0
            else:
                theplayerlist[int(id)-2].support = 1
        formatteams(getbestmatch(playerpool))
    choice = input("would you like to see a list of all possible teams sorted best to worst? (Y/N)\n")
    if choice == "Y" or choice == "y":
        print("1 value at end of team indicates it is a valid 6 core 4 support matchup")
        printbestteamlist(playerpool)
    else:
        return 0
if __name__ == "__main__":
    main()


