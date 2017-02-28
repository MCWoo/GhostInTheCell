import sys
import math

PLAYER_ID_SELF = 1
PLAYER_ID_OPPONENT = -1


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
        print("Starting min distance calculations...", file=sys.stderr)
        for k in range(self.__num_factories):
            for u in range(self.__num_factories):
                for v in range(self.__num_factories):
                    if self.__min_distances[u][v] > (self.__min_distances[u][k] + self.__min_distances[k][v]):
                        self.__min_distances[u][v] = self.__min_distances[u][k] + self.__min_distances[k][v]
                        self.__predecessors[u][v] = self.__predecessors[k][v]       # Take the predecessor from k to v
        print("Finished!", file=sys.stderr)

    # Shortest path from u to v
    def get_path(self, u, v):
        print("Getting path from {} to {}".format(u, v), file=sys.stderr)
        path = []
        k = v
        while k != -1:      # -1 default predecessor for (u,u)
            path.append(k)
            k = self.__predecessors[u][k]
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
            print("Error! Factory {} not in game state!".format(factory_id), file=sys.stderr)
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
            print("Error! Troop owner mismatch: {} vs {}".format(troop, owner), file=sys.stderr)
        if troop.num_cyborgs != num_cyborgs:
            print("Error! Troop cyborg # mismatch: {} vs {}".format(troop, num_cyborgs), file=sys.stderr)
        if troop.source != source:
            print("Error! Troop source mismatch: {} vs {}".format(troop, source), file=sys.stderr)
        if troop.destination != destination:
            print("Error! Troop destination mismatch: {} vs {}".format(troop, destination), file=sys.stderr)
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
            t_me = t_opponent = 0
            for troop_id in troops:
                if self.troops[troop_id].owner == PLAYER_ID_SELF:
                    t_me += self.troops[troop_id].num_cyborgs
                else:
                    t_opponent += self.troops[troop_id].num_cyborgs
            if t_me < t_opponent:
                troop_owner = PLAYER_ID_OPPONENT
                troop_cyborgs = t_opponent-t_me
            elif t_me > t_opponent:
                troop_owner = PLAYER_ID_SELF
                troop_cyborgs = t_me-t_opponent
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

    def get_sorted_factory_list(self):
        return sorted([factory for factory in self.factories if self.factories[factory].cyborg_rate != 0],
                      key=lambda x: self.factories[x].cyborg_rate, reverse=True)

    def get_filtered_factory_list(self):
        return [factory for factory in self.factories if self.factories[factory].cyborg_rate != 0 and self.factories[factory].owner != PLAYER_ID_SELF]

    def get_compliment_filtered_list(self):
        return [factory for factory in self.factories if self.factories[factory].cyborg_rate == 0 and self.factories[factory].owner != PLAYER_ID_SELF]


factory_count = int(input())  # the number of factories
link_count = int(input())  # the number of links between factories

game_state = GameState(factory_count)

for i in range(factory_count):
    game_state.factories[i] = Factory(i)

for i in range(link_count):
    factory_1, factory_2, distance = [int(j) for j in input().split()]
    game_state.factories[factory_1].distances[factory_2] = distance     # Undirected
    game_state.factories[factory_2].distances[factory_1] = distance
    game_state.min_distances.create_edge(factory_1, factory_2, distance)
    game_state.min_distances.create_edge(factory_2, factory_1, distance)       # Undirected

game_state.min_distances.calculate()

# game loop
while True:
    print("Starting turn...", file=sys.stderr)
    entity_count = int(input())  # the number of entities (e.g. factories and troops)
    for i in range(entity_count):
        line = input()
        entity_id, entity_type, arg_1, arg_2, arg_3, arg_4, arg_5 = line.split()
        entity_id = int(entity_id)
        arg_1 = int(arg_1)
        arg_2 = int(arg_2)
        arg_3 = int(arg_3)
        arg_4 = int(arg_4)
        arg_5 = int(arg_5)

        if entity_type == "FACTORY":
            game_state.update_factory(entity_id, owner=arg_1, num_cyborgs=arg_2, cyborg_rate=arg_3)
        elif entity_type == "TROOP":
            game_state.update_troop(troop_id=entity_id,
                                    owner=arg_1,
                                    num_cyborgs=arg_4,
                                    source=arg_2,
                                    destination=arg_3,
                                    time_left=arg_5)
        else:
            print("Error! Bad input: {}".format(entity_type), file=sys.stderr)

    print("Filtering factory", file=sys.stderr)
    filtered_list = game_state.get_filtered_factory_list()
    if not filtered_list:
        filtered_list = game_state.get_compliment_filtered_list()

    print("Getting my factories", file=sys.stderr)
    myfactories = game_state.get_player_factories(PLAYER_ID_SELF)

    source_factory_id = max(myfactories, key=lambda x: game_state.factories[x].num_cyborgs)
    print("Source: {}".format(source_factory_id), file=sys.stderr)
    target_factory_id = -1
    num_cyborgs = 0
    source_factory = game_state.factories[source_factory_id]
    closest_dist = math.inf

    for factory in filtered_list:
        if game_state.factories[factory].num_cyborgs < source_factory.num_cyborgs:
            distance = game_state.min_distances.get_distance(source_factory.id, factory)
            if distance < closest_dist:
                print("Closer: {}, dist: {}".format(factory, distance), file=sys.stderr)
                target_factory_id = factory
                closest_distance = distance
                num_cyborgs = game_state.factories[factory].num_cyborgs + game_state.factories[factory].cyborg_rate*distance
    if target_factory_id == -1:
        print("WAIT")
    else:
        print("MOVE {} {} {}".format(source_factory_id, target_factory_id, num_cyborgs))

    # def closest_able(factoryid):
    #     closest_dist = math.inf
    #     closest_factory_id = -1
    #     cyborgs_needed = math.inf
    #     for myfactory in myfactories:
    #         distance = game_state.min_distances.get_distance(myfactory, factoryid)
    #         cyborgs_needed = game_state.factories[factoryid].num_cyborgs #game_state.cyborgs_at_factory(factoryid, distance) + 1
    #         if game_state.factories[myfactory].num_cyborgs >= cyborgs_needed  and \
    #                         distance < closest_dist:
    #             closest_dist = distance
    #             closest_factory_id = myfactory
    #     return closest_dist, closest_factory_id, cyborgs_needed

    # print("Mapping closest factories", file=sys.stderr)
    # paths = list(map(closest_able, priority_sorted))
    # paths.sort(key=lambda x: x[0])
    # for i in range(len(filtered_list)):
    #     target = filtered_list[i]
    #     dist, factoryid, cyborgs = closest_able(target)
    #     filtered_list[i] = (target, dist, factoryid, cyborgs)

    # closest_dist = math.inf
    # source_factory = None
    # send_cyborgs = 0
    # target_factory = None
    # print("Finding closest path", file=sys.stderr)
    # answer = min(filtered_list, key=lambda x: x[1])
    # for target, dist, source, cyborgs in filtered_list:
    #     if dist < closest_dist:
    #         print("Closest path found!", file=sys.stderr)
    #         source_factory = source
    #         target_factory = target
    #         send_cyborgs = cyborgs
    #         break
    # if not answer:  # source_factory:
    #     print("WAIT")
    #     continue
    #
    # path = game_state.min_distances.get_path(u=answer[2], v=answer[0])
    # print("MOVE {} {} {}".format(path[0], path[1], send_cyborgs))

    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)

    # Any valid action, such as "WAIT" or "MOVE source destination cyborgs"
