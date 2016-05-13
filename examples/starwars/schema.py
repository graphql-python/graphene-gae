from google.appengine.ext import ndb

import graphene
from graphene import relay, resolve_only_args
from graphene_gae import NdbNode, NdbConnectionField

from .data import (create_ship)

from .models import Character as CharacterModel
from .models import Faction as FactionModel
from .models import Ship as ShipModel

schema = graphene.Schema(name='Starwars GAE Relay Schema')


class Ship(NdbNode):
    class Meta:
        model = ShipModel


class Character(NdbNode):
    class Meta:
        model = CharacterModel


class Faction(NdbNode):
    class Meta:
        model = FactionModel

    ships = NdbConnectionField(Ship)

    def resolve_ships(self, args, info):
        return ShipModel.query().filter(ShipModel.faction_key == self.key)


class IntroduceShip(relay.ClientIDMutation):
    class Input:
        ship_name = graphene.String(required=True)
        faction_id = graphene.String(required=True)

    ship = graphene.Field(Ship)
    faction = graphene.Field(Faction)

    @classmethod
    def mutate_and_get_payload(cls, input, info):
        ship_name = input.get('ship_name')
        faction_id = input.get('faction_id')
        faction_key = ndb.Key(FactionModel, faction_id)
        ship = create_ship(ship_name, faction_key)
        faction = faction_key.get()
        return IntroduceShip(ship=Ship(ship), faction=Faction(faction))


class Query(graphene.ObjectType):
    rebels = graphene.Field(Faction)
    empire = graphene.Field(Faction)
    node = relay.NodeField()
    # ships = relay.ConnectionField(Ship, description='All the ships.')
    ships = NdbConnectionField(Ship)

    @resolve_only_args
    def resolve_ships(self):
        return ShipModel.query()

    @resolve_only_args
    def resolve_rebels(self):
        return Faction(FactionModel.get_by_id("rebels"))

    @resolve_only_args
    def resolve_empire(self):
        return Faction(FactionModel.get_by_id("empire"))


class Mutation(graphene.ObjectType):
    introduce_ship = graphene.Field(IntroduceShip)


# We register the Character Model because if not would be
# inaccessible for the schema
schema.register(Character)

schema.query = Query
schema.mutation = Mutation
