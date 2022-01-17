def listcopy(lista, listb):
    for ele in lista:
        listb.append(ele)

def rest(list):
    return(list[1:len(list)])

def listextend(l, list, a, b):
    list1 = []
    list2 = []
    listcopy(list, list1)
    listcopy(list, list2)

    var0 = []
    var1 = []
    var0.append(0)
    var1.append(1)


    if len(list) == l:
        listofmaps.append(list)
    if a > 0:
        list1.extend(var0)
    if b > 0:
        list2.extend(var1)
    if a > 0:
        listextend(l, list1, (a-1), b)
    if b > 0:
        listextend(l, list2, a, (b-1))


def genmap(length):
    global listofmaps
    print("\ngenerating team maps...\n")
    listofmaps = []
    if length % 2 != 0:
        print("length must be an even number")
    else:
        listextend(length, [], length/2, length/2)
    print("team map generation complete\n")
    return listofmaps[0:int(len(listofmaps)/2)]


def maptoteam(map, pool):
    team1 = []
    team2 = []
    teams = [team1, team2]
    for player in pool:
        if map[0] == 0:
            team1.append(player)
        if map[0] == 1:
            team2.append(player)
        map = rest(map)
    return teams


def genteamlist(pool):
    poolsize = len(pool)
    teamlist = []
    maplist = genmap(poolsize)
    for map in maplist:
        teamlist.append(maptoteam(map, pool))
    return teamlist

