import sys
import math

import datetime

PLAYER_ID_SELF = 1
PLAYER_ID_NEUTRAL = 0
PLAYER_ID_OPPONENT = -1

CMD_MOVE = "MOVE"
CMD_WAIT = "WAIT"
CMD_BOMB = "BOMB"


#################################################################################
class Command:
    __id = 0

    def __init__(self, src=-1, dst=-1, time_left=0):
        self.id = self.__id
        self.__id += 1
        self.src = src
        self.dst = dst
        self.time_left = time_left

    def __repr__(self):
        return "{} {} {}".format(CMD_MOVE, self.src, self.dst)

    def __str__(self):
        return "{} {} {}".format(CMD_MOVE, self.src, self.dst)


#################################################################################
class Timer:
    __id = 0

    def __init__(self):
        self.__timers = {}    # id -> datetime

    def reserve_id(self):
        return self.__id

    def start(self, i=__id):
        self.__timers[i] = datetime.datetime.now()
        if i == self.__id:
            self.__id += 1
        return i

    def stop(self, i):
        delta = self.delta(i)
        del self.__timers[i]
        return delta

    def delta(self, i):
        return datetime.datetime.now() - self.__timers[i]

    def clear(self, i):
        if i in self.__timers:
            del self.__timers[i]

timer = Timer()


#################################################################################
# Factory related data
class Factory:
    def __init__(self, factory_id):
        self.owner = 0      # 1 = me, -1 = opponent, 0 = neutral
        self.id = factory_id
        self.cyborg_rate = 0
        self.num_cyborgs = 0

    def __str__(self):
        return "Player {}'s factory ({}): production rate: {}, # cyborgs: {}"\
            .format(self.owner,
                    self.id,
                    self.cyborg_rate,
                    self.num_cyborgs)


#################################################################################
# Troop related data
class Troop:
    def __init__(self, owner, num_cyborgs, src, dst, time_left):
        self.owner = owner
        self.num_cyborgs = num_cyborgs
        self.src = src
        self.dst = dst
        self.time_left = time_left

    def __str__(self):
        return "Player {}'s troop: {} cyborgs moving from {} to {} with {} turns left".format(self.owner,
                                                                                              self.num_cyborgs,
                                                                                              self.src,
                                                                                              self.dst,
                                                                                              self.time_left)


#################################################################################
class MinFactoryDistances:
    def __init__(self, num_factories):
        self.__min_distances = [[(math.inf if m != n else 0) for n in range(num_factories)] for m in range(num_factories)]
        self.__predecessors = [[-1 for n in range(num_factories)] for m in range(num_factories)]
        self.__num_factories = num_factories
        self.__cached_paths = {}    # (u,v) -> [path]

    def create_edge(self, u, v, dist):
        self.__min_distances[u][v] = dist
        self.__predecessors[u][v] = u   # identity

    def get_distance(self, u, v):
        return self.__min_distances[u][v]

    # Floyd-Warshall algorithm
    def calculate(self):
        # print("Min dist: {}".format(self.__min_distances))
        # print("Starting min distance calculations...", file=sys.stderr)
        for k in range(self.__num_factories):
            for u in range(self.__num_factories):
                for v in range(self.__num_factories):
                    if self.__min_distances[u][v] > (self.__min_distances[u][k] + self.__min_distances[k][v]):
                        self.__min_distances[u][v] = self.__min_distances[u][k] + self.__min_distances[k][v]
                        self.__predecessors[u][v] = self.__predecessors[k][v]       # Take the predecessor from k to v
        # print("Min dist: {}".format(self.__min_distances))
        # print("Pred: {}".format(self.__predecessors))
        # print("Finished!", file=sys.stderr)

    # Shortest path from u to v
    def __get_path(self, u, v):
        path = []
        k = v
        while k != -1:      # -1 default predecessor for (u,u)
            path.append(k)
            k = self.__predecessors[u][k]
        return path[::-1]

    def cache_all_paths(self):
        for u in range(self.__num_factories):
            for v in range(self.__num_factories):
                self.__cached_paths[(u, v)] = self.__get_path(u, v)

    def get_cached_path(self, u, v):
        return self.__cached_paths[(u, v)]


#################################################################################
# Holds the game state
class GameState:
    def __init__(self, num_factories):
        factory_range = range(num_factories)
        self.factories = {}     # id -> Factory Node
        self.troops = {}
        self.min_distances = MinFactoryDistances(num_factories)
        self.original_graph = [[(math.inf if m != n else 0) for n in factory_range] for m in factory_range]
        self.future_commands = []

    def create_edge(self, u, v, dist):
        self.original_graph[u][v] = dist
        self.min_distances.create_edge(u, v, dist)

    # Change the data for a given factory
    def update_factory(self, factory_id, owner, num_cyborgs, cyborg_rate):
        factory = self.factories[factory_id]
        factory.owner = owner
        factory.num_cyborgs = num_cyborgs
        factory.cyborg_rate = cyborg_rate

    # Change or add the data for a given troop
    def update_troop(self, troop_id, owner, num_cyborgs, src, dst, time_left):
        if troop_id not in self.troops:
            self.troops[troop_id] = Troop(owner=owner,
                                          num_cyborgs=num_cyborgs,
                                          src=src,
                                          dst=dst,
                                          time_left=time_left)
            return
        self.troops[troop_id].time_left = time_left

    # Update all future commands
    def tick_commands(self):
        for cmd in self.future_commands:
            cmd.time_left -= 1

    def prune_commands(self):
        self.future_commands = [cmd for cmd in self.future_commands if cmd]

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
            if troop.time_left <= turns_later and troop.dst == factory_id:
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

    def can_run_command(self, command):
        return self.factories[command.src].num_cyborgs >= command.cyborgs

    def cyborgs_on_path(self, u, v):
        path = self.min_distances.get_cached_path(u, v)
        troops = 0
        for k in range(len(path)-1):
            dist = self.min_distances.get_distance(path[k], path[k+1])
            if self.factories[path[k+1]].owner == PLAYER_ID_SELF:
                # troops -= self.factories[path[k+1]].num_cyborgs
                # troops -= self.factories[path[k+1]].cyborg_rate*(dist+1)
                continue
            troops += self.factories[path[k+1]].num_cyborgs
            if self.factories[path[k+1]].owner == PLAYER_ID_OPPONENT:
                troops += self.factories[path[k+1]].cyborg_rate*(dist+1)
        return troops

    def get_edge(self, u, v):
        return self.original_graph[u][v]


factory_count = int(input())  # the number of factories
link_count = int(input())  # the number of links between factories

state = GameState(factory_count)

for i in range(factory_count):
    state.factories[i] = Factory(i)

for i in range(link_count):
    factory_1, factory_2, distance = [int(j) for j in input().split()]
    state.create_edge(factory_1, factory_2, distance)
    state.create_edge(factory_2, factory_1, distance)       # Undirected

init_timer = timer.start()
state.min_distances.calculate()
state.min_distances.cache_all_paths()

delta = timer.stop(init_timer)
print("{:.2f} ms spent initializing".format(delta.microseconds / 1000.0), file=sys.stderr)
loop_timer = timer.reserve_id()

# game loop
while True:
    game_cmd = "MSG Mommy said not to talk to  strangers..."
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
            state.update_factory(entity_id, owner=arg_1, num_cyborgs=arg_2, cyborg_rate=arg_3)
        elif entity_type == "TROOP":
            state.update_troop(troop_id=entity_id,
                               owner=arg_1,
                               num_cyborgs=arg_4,
                               src=arg_2,
                               dst=arg_3,
                               time_left=arg_5)
        elif entity_type == "BOMB":
            print("BOMB", file=sys.stderr)

    timer.start(loop_timer)

    state.tick_commands()

    # Check commands to execute
    remove_cmds = []    # indices to remove
    for i in range(len(state.future_commands)):
        cmd = state.future_commands[i]
        if cmd and cmd.time_left < 0:
            if state.factories[cmd.src].owner == PLAYER_ID_OPPONENT:
                state.future_commands[i] = None
                continue
            cyborgs_needed = state.cyborgs_on_path(cmd.src, cmd.dst) + 1
            if state.factories[cmd.src].num_cyborgs >= cyborgs_needed:
                path = state.min_distances.get_cached_path(cmd.src, cmd.dst)
                print("Path: {}".format(path), file=sys.stderr)
                game_cmd += ";{} {} {} {}".format(CMD_MOVE, cmd.src, path[1], cyborgs_needed)
                state.factories[cmd.src].num_cyborgs -= cyborgs_needed
                if len(path) > 2:
                    state.future_commands[i].src = path[1]
                    state.future_commands[i].time_left = state.get_edge(cmd.src, path[1])
                else:
                    state.future_commands[i] = None
            else:
                state.future_commands[i] = None

    state.prune_commands()

    # print("Filtering factory", file=sys.stderr)
    filtered_list = state.get_filtered_factory_list()
    # print("Filtered list: {}".format(filtered_list), file=sys.stderr)
    if not filtered_list:
        filtered_list = state.get_compliment_filtered_list()
        # print("Filtered list: {}".format(filtered_list), file=sys.stderr)

    # print("Getting my factories", file=sys.stderr)
    myfactories = state.get_player_factories(PLAYER_ID_SELF)
    if not myfactories:
        print("WAIT")
        continue

    source_factory_id = max(myfactories, key=lambda x: state.factories[x].num_cyborgs)
    # print("Source: {}".format(source_factory_id), file=sys.stderr)
    target_factory_id = -1
    num_cyborgs = 0
    source_factory = state.factories[source_factory_id]
    closest_dist = math.inf

    for factory in filtered_list:
        rate = state.factories[factory].cyborg_rate
        distance = state.min_distances.get_distance(source_factory.id, factory)
        cyborgs_needed = state.cyborgs_on_path(source_factory_id, factory) + 1
        if cyborgs_needed <= source_factory.num_cyborgs:
            if distance < closest_dist:
                target_factory_id = factory
                closest_dist = distance
                num_cyborgs = cyborgs_needed
    if target_factory_id == -1:
        game_cmd += ";WAIT"
    elif num_cyborgs <= 0:
        path = state.min_distances.get_cached_path(u=source_factory_id, v=target_factory_id)
        if len(path) > 2:
            state.future_commands.append(Command(src=path[1], dst=target_factory_id, time_left=1))
    else:
        path = state.min_distances.get_cached_path(u=source_factory_id, v=target_factory_id)
        game_cmd += ";MOVE {} {} {}".format(source_factory_id, path[1], num_cyborgs)
        if len(path) > 2:
            state.future_commands.append(Command(src=path[1], dst=target_factory_id,
                                                 time_left=state.get_edge(source_factory_id, path[1])))

    print(game_cmd)
    delta = timer.delta(loop_timer)
    print("{:.2f} ms spent on turn".format(delta.microseconds / 1000.0), file=sys.stderr)
