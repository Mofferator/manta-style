import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
client = gspread.authorize(creds)

sheet = client.open("Balancer Bot Test Spreadsheet").worksheet("Sheet2")

global playerrecords
playerrecords = sheet.get_all_records()


def ingestrecords():
    from player import player
    c = 2
    playerlist = []
    for ele in playerrecords:
        p = player(c, ele["mmr"], ele["real mmr"], ele["Name"], ele["support?"], ele["id"])
        playerlist.append(p)
        c += 1
    return playerlist


playerlist = ingestrecords()


def findlastrow():
    return len(playerlist) + 2

def listofplayerids():
    playeridlist = []
    for player in playerlist:
        playeridlist.append(player.steamid)
    return playeridlist

playeridlist = listofplayerids()

def updateplayer(name, steamid, support, mmroverride):
    print("Updating Spreadsheet")
    row = findlastrow()
    sheet.update_cell(row, 1, name)
    sheet.update_cell(row, 4, support)
    sheet.update_cell(row, 5, steamid)
    sheet.update_cell(row, 6, mmroverride)
    print("{} added".format(name))

def main():
    steamid = input("Enter the player's Steam ID (can be found on their dota profile)\n")
    if int(steamid) in playeridlist:
        print("This player is already in the spreadsheet")
        response = input("Would you like to add a different player? (Y/N)")
        if response == "Y" or response == "y":
            main()
        else:
            return 0
    else:
        name = input("Enter player's name: ")
        def checksupport():
            support = input("Can this player play support? (Y/N)")
            if support == "Y" or support == "y":
                return  1
            elif support == "N" or support == "n":
                return  0
            else:
                print("invalid input, please answer Y/N")
                checksupport()
        supportbool = checksupport()

        mmroverride = input("Enter mmr override if they need one (if immortal, then they do)\nIf not just press enter\n")
        updateplayer(name, steamid, supportbool, mmroverride)
        response = input("Would you like to add a different player? (Y/N)")
        if response == "Y" or response == "y":
            main()
        else:
            return 0

if __name__ == "__main__":
    main()