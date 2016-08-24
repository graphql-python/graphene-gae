from google.appengine.ext import ndb

import graphene
from graphene import relay, resolve_only_args
from graphene_gae import NdbObjectType, NdbConnectionField

from .data import create_ship

from .models import Character as CharacterModel
from .models import Faction as FactionModel
from .models import Ship as ShipModel


class Ship(NdbObjectType):
    class Meta:
        model = ShipModel
        interfaces = (relay.Node,)


class Character(NdbObjectType):
    class Meta:
        model = CharacterModel
        interfaces = (relay.Node,)


class Faction(NdbObjectType):
    class Meta:
        model = FactionModel
        interfaces = (relay.Node,)

    ships = NdbConnectionField(Ship)

    def resolve_ships(self, *_):
        return ShipModel.query().filter(ShipModel.faction_key == self.key)


class IntroduceShip(relay.ClientIDMutation):
    class Input:
        ship_name = graphene.String(required=True)
        faction_id = graphene.String(required=True)

    ship = graphene.Field(Ship)
    faction = graphene.Field(Faction)

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
        ship_name = input.get('ship_name')
        faction_id = input.get('faction_id')
        faction_key = ndb.Key(FactionModel, faction_id)
        ship = create_ship(ship_name, faction_key)
        faction = faction_key.get()
        return IntroduceShip(ship=ship, faction=faction)


class Query(graphene.ObjectType):
    rebels = graphene.Field(Faction)
    empire = graphene.Field(Faction)
    node = relay.Node.Field()
    ships = NdbConnectionField(Ship)

    @resolve_only_args
    def resolve_ships(self):
        return ShipModel.query()

    @resolve_only_args
    def resolve_rebels(self):
        return FactionModel.get_by_id("rebels")

    @resolve_only_args
    def resolve_empire(self):
        return FactionModel.get_by_id("empire")


class Mutation(graphene.ObjectType):
    introduce_ship = IntroduceShip.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
