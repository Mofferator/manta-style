import urllib3
import json
import os
from dotenv import load_dotenv

load_dotenv('.ENV')
KEY = os.getenv("OPENDOTAKEY")

http = urllib3.PoolManager()
class player(object):
    def __init__(self, playerid, mmr, realmmr, name, support, steamid):
        self.playerid=playerid
        self.mmr = mmr
        self.realmmr = realmmr
        self.name = name
        self.support = support
        self.steamid = steamid
    def avatar(self):
        a = http.request("GET", "https://api.opendota.com/api/players/"
                            + str(self.steamid)
                            + "?api_key=" + KEY)
        avatar = json.loads(a.data)["profile"]["avatarfull"]
        return str(avatar)


if __name__ == '__main__':
    playertest = player(2, 4000, 4000, "Moff", 1, 108305168)
    print(playertest.avatar())