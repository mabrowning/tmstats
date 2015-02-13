#!/usr/bin/env python
import json, cPickle as pickle, os.path, numpy, sys, copy
from collections import defaultdict
from welford import Welford

GAME_PATH="games/"

GAME_LIST_FILENAME = "gamelist.pickle"
GAME_FILENAME = "games.pickle"

class FactionStat(object):
    def __init__(self, game, name ):
        self.name = name
        self.user  = game["factions"][name]["username"]
        self.score = game["factions"][name]["VP"]
        self.vp_source = game["factions"][name]["vp_source"]
        self.events = game["events"]["faction"][name]
        self.parse_events()
        del self.events #don't need this anymore!

    def parse_event(self, evt ):
        if evt not in self.events:
            return numpy.zeros( 7 )
        r = defaultdict(int,self.events[evt]["round"])
        return numpy.array((r["0"],r["1"],r["2"],r["3"],r["4"],r["5"],r["6"] ))

    def parse_favor( self, num ):
        key = "favor:FAV"+str(num)
        if key not in self.events:
            return 0
        r = self.events[key]["round"].keys()
        r.remove("all")
        return int(r[0])

    def parse_town( self, num ):
        key = "town:TW"+str(num)
        if key not in self.events:
            return 0
        r = self.events[key]["round"].keys()
        r.remove("all")
        return int(r[0])


    def parse_events( self ):
        D_evt  = self.parse_event( "build:D" )
        TP_evt = self.parse_event( "upgrade:TP" )
        TE_evt = self.parse_event( "upgrade:TE" )
        SA_evt = self.parse_event( "upgrade:SA" )
        SH_evt = self.parse_event( "upgrade:SH" )

        #upgrade path...
        D  = numpy.cumsum( D_evt  - TP_evt )
        TP = numpy.cumsum( TP_evt - TE_evt - SH_evt )
        TE = numpy.cumsum( TE_evt - SA_evt )
        SA = numpy.cumsum( SA_evt )
        SH = numpy.cumsum( SH_evt )

        self.B = numpy.array( ( D, TP, TE, SA, SH ), dtype=int )
        self.FAV = numpy.array( [ self.parse_favor( i ) for i in range(1,13) ] )
        self.TW  = numpy.array( [ self.parse_town( i ) for i in range(1,9) ] )

fdict= {u'acolytes': 'a',
 u'alchemists': 'b',
 u'auren': 'c',
 u'chaosmagicians': 'd',
 u'cultists': 'e',
 u'darklings': 'f',
 u'dragonlords': 'g',
 u'dwarves': 'h',
 u'engineers': 'i',
 u'fakirs': 'j',
 u'giants': 'k',
 u'halflings': 'l',
 u'icemaidens': 'm',
 u'mermaids': 'n',
 u'nomads': 'o',
 u'riverwalkers': 'p',
 u'shapeshifters': 'q',
 u'swarmlings': 'r',
 u'witches': 's',
 u'yetis': 't'}

def get_key( faction, numplayers ):
    key  = fdict[faction.name]
    key += str( numplayers )
    key += str( get_rating( faction.user, faction.name ))
    key += "".join( str(i) for i in tuple(faction.B[:,1]))
    key += "".join( hex(i+1)[-2] for i in tuple(numpy.where( faction.FAV == 1 )[0]))
    return key

def load():
    allgames = {}
    #Try to load from pickle
    if os.path.isfile( GAME_FILENAME ):
        with open( GAME_FILENAME ) as game_file:
            print "loading... ",
            sys.stdout.flush()
            allgames = pickle.load( game_file )
            print "done!"
    return allgames

with open( "ratings.json" ) as f:
    ratings = json.load( f )["players"]

def get_rating( player, faction ):
    if player not in ratings:
        return 0
    if faction not in ratings[player]["faction_breakdown"]:
        return 0
    score = ratings[player]["faction_breakdown"][faction]["score"]
    if score < -37:
        return 0
    elif score < 0:
        return 1
    elif score < 37:
        return 2
    else:
        return 3

def parse_game( game ):
    stats = []
    game_fn = GAME_PATH+game+".json"
    if not os.path.isfile( game_fn ):
        return stats

    with open( game_fn ) as game_file:
        try:
            game_json = json.load( game_file )
        except:
            print(game + " had an error in the json!")
            return stats
        if game_json["aborted"]:
            return stats

        print( "parsing " + game + "..." )
        for faction in game_json["factions"].keys():
            try:
                if "dropped" in game_json["factions"][faction]:
                    continue
                s =  FactionStat( game_json, faction ) 
                stats.append( s )
            except KeyError,e :
                print( game_fn + " failed! ("+faction+" didn't have "+str(e.args)+")" )
    return stats

def refresh_games( allgames = {} ):
    game_list = []
    #Try to load from pickle
    if os.path.isfile( GAME_LIST_FILENAME ):
        with open( GAME_LIST_FILENAME ) as game_list_file:
            game_list = pickle.load( game_list_file )

    for game in game_list:
        try:
            if game not in allgames:
                g = parse_game( game )
                if g:
                    allgames[game] = g
        except KeyboardInterrupt, e:
            break

    print "saving... ",
    sys.stdout.flush()
    with open( GAME_FILENAME, "w+" ) as game_file:
        pickle.dump( allgames, game_file ) 
    print( "done!")
    return allgames


def get_statpool( allgames, statfuncs ):
    statpool = {}
    statbase = [ Welford() for x in statfuncs ]
    for game,factions in allgames.items():
        for faction in factions:
            key  = get_key(faction,len(factions))
            stats = statpool.setdefault( key, copy.deepcopy( statbase ) )
            for i,statfunc in enumerate(statfuncs):
                stats[i]( statfunc( factions, faction ) )
    return statpool

def get_game_avg_score( factions, faction ):
    avg = float(sum( f.score  for f in factions )) / len( factions )
    return faction.score - avg


def compute_vp_stats( allgames ):
    vp_stats = {}
    vp_factstats = {}
    for game,factions in allgames.items():
        for faction in factions:
            for source,vp in faction.vp_source.items():
                vp_stats.setdefault(source,Welford())(vp)
                vp_factstats.setdefault(faction.name,dict()).setdefault(source,Welford())(vp)
    return vp_stats, vp_factstats

def compute_stats( allgames ):
    return get_statpool( allgames, [ lambda game,fact: float(fact.score), get_game_avg_score ] )

def save_stats( statpool, filename = "stats.json" ):
    def jsonify( x ):
        if x.n == 1:
            return int(10*x.M1)
        else:
            return [x.n,int(10*x.M1),int(10*x.M2),int(10*x.M3),int(10*x.M4)]

    with open( filename, "w+") as f:
        json.dump( statpool, f, default = jsonify )

if __name__ == "__main__":
    allgames = load()
    statpool = compute_stats( allgames )
    save_stats( statpool )
