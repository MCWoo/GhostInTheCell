import sys
import math


# Factory related data
class Factory:
    def __init__(self, factory_id):
        self.owner = 0      # 1 = me, -1 = opponent, 0 = neutral
        self.id = factory_id
        self.cyborg_rate = 0
        self.num_cyborgs = 0
        self.distances = {}     # factory_id -> distance

    def __str__(self):
        return "Player {}'s factory ({}): production rate: {}, # cyborgs: {}, adjacency list: {}"\
            .format(self.owner,
                    self.id,
                    self.cyborg_rate,
                    self.num_cyborgs,
                    self.distances)


# Troop related data
class Troop:
    def __init__(self, owner, num_cyborgs, source, destination, time_left):
        self.owner = owner
        self.num_cyborgs = num_cyborgs
        self.source = source
        self.destination = destination
        self.time_left = time_left

    def __str__(self):
        return "Player {}'s troop: {} cyborgs moving from {} to {} with {} turns left".format(self.owner,
                                                                                              self.num_cyborgs,
                                                                                              self.source,
                                                                                              self.destination,
                                                                                              self.time_left)


class MinFactoryDistances:
    def __init__(self, num_factories):
        self.__min_distances = [[math.inf for n in range(num_factories)] for m in range(num_factories)]
        self.__predecessors = [[-1 for n in range(num_factories)] for m in range(num_factories)]
        self.__num_factories = num_factories

    def create_edge(self, u, v, dist):
        self.__min_distances[u][v] = dist
        self.__predecessors[u][v] = u   # identity

    def get_distance(self, u, v):
        return self.__min_distances[u][v]

    # Floyd-Warshall algorithm
    def calculate(self):
        for k in range(self.__num_factories):
            for u in range(self.__num_factories):
                for v in range(self.__num_factories):
                    if self.__min_distances[u][v] > (self.__min_distances[u][k] + self.__min_distances[k][v]):
                        self.__min_distances[u][v] = self.__min_distances[u][k] + self.__min_distances[k][v]
                        self.__predecessors[u][v] = self.__predecessors[k][v]       # Take the predecessor from k to v

    # Shortest path from u to v
    def get_path(self, u, v):
        path = []
        k = v
        while k != -1:      # -1 default predecessor for (u,u)
            path.append(k)
            k = self.__predecessors[u,k]
        return path.reverse()


# Holds the game state
class GameState:
    def __init__(self, num_factories):
        self.factories = {}     # id -> Factory Node
        self.troops = {}
        self.min_distances = MinFactoryDistances(num_factories)

    # Change the data for a given factory
    def update_factory(self, factory_id, owner, num_cyborgs, cyborg_rate):
        if factory_id not in self.factories:
            print("Error! Factory {} not in game state!".format(factory_id))
        factory = self.factories[factory_id]
        factory.owner = owner
        factory.num_cyborgs = num_cyborgs
        factory.cyborg_rate = cyborg_rate

    # Change or add the data for a given troop
    def update_troop(self, troop_id, owner, num_cyborgs, source, destination, time_left):
        if troop_id not in self.troops:
            self.troops[troop_id] = Troop(owner=owner,
                                          num_cyborgs=num_cyborgs,
                                          source=source,
                                          destination=destination,
                                          time_left=time_left)
            return
        troop = self.troops[troop_id]
        if troop.owner != owner:
            print("Error! Troop owner mismatch: {} vs {}".format(troop), owner)
        if troop.num_cyborgs != num_cyborgs:
            print("Error! Troop cyborg # mismatch: {} vs {}".format(troop), num_cyborgs)
        if troop.source != source:
            print("Error! Troop source mismatch: {} vs {}".format(troop), source)
        if troop.destination != destination:
            print("Error! Troop destination mismatch: {} vs {}".format(troop), destination)
        troop.time_left = time_left     # Should be the only thing to change

    # Get all factories that a player owns
    def get_player_factories(self, player_id):
        owned_factories = []
        for factory_id, factory in self.factories.items():
            if factory.owner == player_id:
                owned_factories.append(factory_id)
        return owned_factories

    # Get the number of cyborgs at the factory a certain number of turns later
    def cyborgs_at_factory(self, factory_id, turns_later=0):
        num_cyborgs = self.factories[factory_id].num_cyborgs
        factory_owner = self.factories[factory_id].owner
        cyborg_rate = self.factories[factory_id].cyborg_rate

        inbound_troops = {}
        for troop_id, troop in self.troops.items():
            if troop.time_left <= turns_later and troop.destination == factory_id:
                if troop.time_left in inbound_troops:
                    inbound_troops[troop.time_left].append(troop_id)
                else:
                    inbound_troops[troop.time_left] = [troop_id]

        # calculate
        last_check = 0
        for time_left, troops in sorted(inbound_troops.items()):
            num_cyborgs = 0

            # If not neutral, produce cyborgs
            if factory_owner != 0:
                num_cyborgs += (troops[0].time_left - last_check) * cyborg_rate

            # resolve multiple troops fighting
            t1 = t2 = 0
            for troop_id in troops:
                if self.troops[troop_id].owner == -1:
                    t1 += self.troops[troop_id].num_cyborgs
                else:
                    t2 += self.troops[troop_id].num_cyborgs
            if t1 < t2:
                troop_owner = 1
                troop_cyborgs = t2-t1
            elif t1 > t2:
                troop_owner = -1
                troop_cyborgs = t1-t2
            else:       # Equal, no change
                continue

            # Calculate troop contribution
            if troop_owner == factory_owner:
                num_cyborgs += troop_cyborgs
            else:
                num_cyborgs -= troop_cyborgs
                if num_cyborgs < 0:
                    num_cyborgs = abs(num_cyborgs)
                    factory_owner *= -1     # cheap way to change owners ASSUMING only -1 and 1
            last_check = troops[0].time_left
        return num_cyborgs



# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

factory_count = int(input())  # the number of factories
link_count = int(input())  # the number of links between factories

game_state = GameState()
game_state.min_distances = MinFactoryDistances(factory_count)

for i in range(0, factory_count):
    game_state.factories[i] = Factory(i)

for i in range(link_count):
    factory_1, factory_2, distance = [int(j) for j in input().split()]
    game_state.factories[factory_1].distances[factory_2] = distance     # Undirected
    game_state.factories[factory_2].distances[factory_1] = distance
    min_distances.create_edge(factory_1, factory_2, distance)
    min_distances.create_edge(factory_2, factory_1, distance)       # Undirected

game_state.min_distances.calculate()

# game loop
while True:
    entity_count = int(input())  # the number of entities (e.g. factories and troops)
    for i in range(entity_count):
        entity_id, entity_type, arg_1, arg_2, arg_3, arg_4, arg_5 = input().split()
        entity_id = int(entity_id)
        arg_1 = int(arg_1)
        arg_2 = int(arg_2)
        arg_3 = int(arg_3)
        arg_4 = int(arg_4)
        arg_5 = int(arg_5)

        if entity_type == "FACTORY":
            game_state.change_factory_data(entity_id, owner=arg_1, num_cyborgs=arg_2, cyborg_rate=arg_3)
        elif entity_type == "TROOP":
            game_state.update_troop(troop_id=entity_id,
                                    owner=arg_1,
                                    num_cyborgs=arg_4,
                                    source=arg_2,
                                    destination=arg_3,
                                    time_left=arg_5)
        else:
            print("Error! Bad input: {}".format(entity_type))

    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)


    # Any valid action, such as "WAIT" or "MOVE source destination cyborgs"
    print("WAIT")
