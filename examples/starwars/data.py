
from .models import Character, Faction, Ship

__author__ = 'ekampf'


def initialize():
    human = Character(name='Human')
    human.put()

    droid = Character(name='Droid')
    droid.put()

    rebels = Faction(id="rebels", name='Alliance to Restore the Republic', hero_key=human.key)
    rebels.put()

    empire = Faction(id="empire", name='Galactic Empire', hero_key=droid.key)
    empire.put()

    xwing = Ship(name='X-Wing', faction_key=rebels.key)
    xwing.put()

    ywing = Ship(name='Y-Wing', faction_key=rebels.key)
    ywing.put()

    awing = Ship(name='A-Wing', faction_key=rebels.key)
    awing.put()

    # Yeah, technically it's Corellian. But it flew in the service of the rebels,
    # so for the purposes of this demo it's a rebel ship.
    falcon = Ship(name='Millenium Falcon', faction_key=rebels.key)
    falcon.put()

    homeOne = Ship(name='Home One', faction_key=rebels.key)
    homeOne.put()

    tieFighter = Ship(name='TIE Fighter', faction_key=empire.key)
    tieFighter.put()

    tieInterceptor = Ship(name='TIE Interceptor', faction_key=empire.key)
    tieInterceptor.put()

    executor = Ship(name='Executor', faction_key=empire.key)
    executor.put()


def create_ship(ship_name, faction_key):
    new_ship = Ship(name=ship_name, faction_key=faction_key)
    new_ship.put()
    return new_ship
