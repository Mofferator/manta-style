import gspread
from player import player
from MatchStats import MatchStats
from oauth2client.service_account import ServiceAccountCredentials
import match_backend


scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
client = gspread.authorize(creds)

sheet = client.open("Balancer Bot Test Spreadsheet").worksheet("Sheet2")
print("\nfetching player records...\n")
playerrecords = sheet.get_all_records()
print("fetch complete\n")
# takes playerrecords and outputs a list of player
# where a player is a list of [ID, ELO, NAME, SUPPORT?]

p = player(1, 2, 3, 4, 5, 6)

def ingestrecords():
    from player import player
    c = 2
    playerlist = []
    for ele in playerrecords:
        p = player(c, ele["mmr"], ele["real mmr"], ele["Name"], ele["support?"], ele["id"])
        playerlist.append(p)
        c += 1
    return playerlist


# creates a dictionary of player steamids and row numbers
# e.g. {12345678 : 2}

playerlist = ingestrecords()
playerdictionary = {}
for player in playerlist:
    playerdictionary[player.steamid] = player.playerid


def listmatchesplayedin(steamid):
    from MatchStats import MatchStats
    playerid = playerdictionary[steamid]
    playerrow = playerrecords[playerid-2]
    matchplayedlist = []
    for mID, result in playerrow.items():
        print(mID, steamid)
        if result == "L" or result == "W":
            matchplayedlist.append([mID, result])
            match = match_backend.requestmatch(mID)
            print
            for player in match.p:
                if player.sid == steamid:
                    matchplayedlist.append(player)
           

    return matchplayedlist



def listids():
    for player in playerlist:
        print(str(player.name) + " ({})".format(player.playerid))

if __name__ == "__main__":
    #print(True)
    print(playerlist[0].name)
    #print(listids())
    #print(listmatchesplayedin(108305168))
