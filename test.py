import random
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
class MessageGenerator:
    __msg_sets = []
    __dork_msgs = ["Mommy said not to talk to  strangers...",
                   "Where to go...                               IDK my BFF Jill?",
                   "Quickly, it's past my                   bedtime!",
                   "I made this with my tears    TT_TT",
                   "Shhh, I'm not supposed to   be on the computer!",
                   "I'm not a robot!",]
    __inspirational_msgs = ["Be the change you wish to   see.",
                            "WWJD?",
                            "Love is patient,                             love is kind",
                            "It is never too late to be      what you might have been.",
                            "To love at all is to be                vulnerable.",
                            "A journey of a thousand     miles begins with one step."]
    __obnoxious_msgs = ["R U SRS??",
                        "LOL",
                        "ROFLROFLROFLROFLROFLROFLROFL",
                        "Is that even a real                      strategy??",
                        "Are you dead yet??",
                        "You. Should. Have. Bought. A. Squirrel.",
                        "GG no re.",
                        "You're done.",
                        "Can you just give up?",
                        "Wat",
                        "/surrender pls",
                        "Hey, alt + f4 gives you an      extra bomb!",
                        "Ctrl + QQ and you win!",]
    __challenge_msgs = ["Get your game on!",
                        "It's time to d-d-d-d-d-duel!",
                        "GL HF",
                        "You ready for this?",
                        "Bug catcher ManTiss wantsto battle!",
                        "It's morphin' time!",
                        "Challenge accepted!",]
    __msg_sets.append(__dork_msgs)
    __msg_sets.append(__inspirational_msgs)
    __msg_sets.append(__obnoxious_msgs)
    __msg_sets.append(__challenge_msgs)

    def __get_rand_wait(self):
        return random.randint(self.__base, self.__base + self.__range)

    def get(self):
        if self.__wait == 0:
            self.__curr_msg = self.__msgs[random.randrange(len(self.__msgs))]
            self.__wait = self.__get_rand_wait()
        else:
            self.__wait -= 1
        return self.__curr_msg

    def __init__(self, base=5, rand_range=7):
        random.seed(datetime.datetime.now().microsecond)
        self.__base = base
        self.__range = rand_range
        self.__wait = 0
        self.__msgs = self.__msg_sets[random.randrange(len(self.__msg_sets))]
        self.__curr_msg = ""


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
        d = self.delta(i)
        del self.__timers[i]
        return d

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
        self.locality = -1

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Player {}'s factory ({}): production rate: {}, # cyborgs: {}"\
            .format(self.owner,
                    self.id,
                    self.cyborg_rate,
                    self.num_cyborgs)

    def __eq__(self, other):
        try:
            if other.__class__.__name__ != "Factory":
                return False
            return other.id == self.id
        except:
            return False


#################################################################################
# Troop related data
class Troop:
    def __init__(self, troop_id, owner, num_cyborgs, src, dst, time_left):
        self.id = troop_id
        self.owner = owner
        self.num_cyborgs = num_cyborgs
        self.src = src
        self.dst = dst
        self.time_left = time_left

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Player {}'s troop ({}): {} cyborgs moving from {} to {} with {} turns left".format(self.owner,
                                                                                                   self.id,
                                                                                                   self.num_cyborgs,
                                                                                                   self.src,
                                                                                                   self.dst,
                                                                                                   self.time_left)

    def __eq__(self, other):
        try:
            if other.__class__.__name__ != "Troop":
                return False
            return other.id == self.id
        except:
            return False


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
        for k in range(self.__num_factories):
            for u in range(self.__num_factories):
                for v in range(self.__num_factories):
                    if self.__min_distances[u][v] > (self.__min_distances[u][k] + self.__min_distances[k][v]):
                        self.__min_distances[u][v] = self.__min_distances[u][k] + self.__min_distances[k][v]
                        self.__predecessors[u][v] = self.__predecessors[k][v]       # Take the predecessor from k to v

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
class PlayerStats:
    def __init__(self):
        self.factories = []
        self.cyborgs = 0
        self.cyborg_rate = 0
        self.bombs = 2

    def clear(self):
        self.factories.clear()
        self.cyborgs = 0
        self.cyborg_rate = 0


#################################################################################
# Holds the game state
class GameState:
    def __init__(self, num_factories):
        factory_range = range(num_factories)
        self.factories = {i: Factory(i) for i in factory_range}     # id -> Factory Node
        self.perceived_factories = {i: Factory(i) for i in factory_range}     # id -> Factory Node
        self.troops = {}        # dst -> troop
        self.min_distances = MinFactoryDistances(num_factories)
        self.original_graph = [[(math.inf if m != n else 0) for n in factory_range] for m in factory_range]
        self.future_commands = []

        self.player_stats = {PLAYER_ID_SELF: PlayerStats(), PLAYER_ID_OPPONENT: PlayerStats()}

    def create_edge(self, u, v, dist):
        self.original_graph[u][v] = dist
        self.min_distances.create_edge(u, v, dist)

    def calculate_locality(self):
        factory_range = range(len(self.factories))
        for u in factory_range:
            for v in factory_range:
                self.factories[u].locality += self.get_edge(u, v)
                self.perceived_factories[u].locality += self.get_edge(u, v)

    # Change the data for a given factory
    def update_factory(self, factory_id, owner, num_cyborgs, cyborg_rate):
        def helper(factory, o, n, r):
            factory.owner = o
            factory.num_cyborgs = n
            factory.cyborg_rate = r

        if owner in self.player_stats:
            self.player_stats[owner].factories.append(factory_id)
            self.player_stats[owner].cyborgs += num_cyborgs
            self.player_stats[owner].cyborg_rate += cyborg_rate

        helper(self.factories[factory_id], owner, num_cyborgs, cyborg_rate)
        helper(self.perceived_factories[factory_id], owner, num_cyborgs, cyborg_rate)

    def next_round(self):
        self.clear_troops()
        self.player_stats[PLAYER_ID_SELF].clear()
        self.player_stats[PLAYER_ID_OPPONENT].clear()

    def clear_troops(self):
        self.troops.clear()

    # Change or add the data for a given troop
    def update_troop(self, troop_id, owner, num_cyborgs, src, dst, time_left):
        self.player_stats[owner].cyborgs += num_cyborgs
        troop = Troop(troop_id=troop_id,
                      owner=owner,
                      num_cyborgs=num_cyborgs,
                      src=src,
                      dst=dst,
                      time_left=time_left)
        if dst not in self.troops:
            self.troops[dst] = {troop_id: troop}
            return
        self.troops[dst][troop_id] = troop

    def update_after_move(self, src, dst, num_cyborgs):
        self.factories[src].num_cyborgs -= num_cyborgs
        self.perceived_factories[src].num_cyborgs -= num_cyborgs    # should be moving from self
        if self.perceived_factories[src].num_cyborgs < 0:
            self.perceived_factories[src].num_cyborgs *= -1
            self.perceived_factories[src].owner *= -1

        dist = self.get_edge(src, dst)

        if self.perceived_factories[dst].owner == PLAYER_ID_SELF:
            self.perceived_factories[dst].num_cyborgs += num_cyborgs
        else:
            if self.perceived_factories[dst].owner == PLAYER_ID_OPPONENT:
                num_cyborgs -= self.perceived_factories[dst].cyborg_rate*(dist+1)
            self.perceived_factories[dst].num_cyborgs -= num_cyborgs
            if self.perceived_factories[dst].num_cyborgs < 0:
                self.perceived_factories[dst].owner = PLAYER_ID_SELF
                self.perceived_factories[dst].num_cyborgs *= -1

    def calculate_perception(self):
        for dst in self.troops:
            # Sort and walk time-wise through troops
            factory = self.perceived_factories[dst]
            troops = [self.troops[dst][troop_id] for troop_id in self.troops[dst]]
            troops.sort(key=lambda t: t.time_left)

            num_troops = len(troops)
            num_skip = 0
            last_update = 0
            for i in range(num_troops):
                if num_skip > 0:
                    num_skip -= 1
                    continue
                troop = troops[i]
                delta = troop.num_cyborgs * troop.owner # delta w.r.t. me owning the factory
                # if multiple troops arrive at the same time
                for j in range(i+1, num_troops):
                    if troops[j].time_left == troop.time_left:
                        delta += troops[j].num_cyborgs * troop.owner
                        num_skip += 1
                    else:
                        break

                # If not neutral, generates troops
                if factory.owner == PLAYER_ID_NEUTRAL:
                    factory.num_cyborgs -= abs(delta)
                else:
                    delta *= factory.owner  # -troops = opponent won, but add them if opponent is owner, else subtract
                    factory.num_cyborgs += factory.cyborg_rate*(troop.time_left-last_update)
                    factory.num_cyborgs += delta
                # Ownership change perceived
                if factory.num_cyborgs < 0:
                    factory.num_cyborgs *= -1
                    if factory.owner == PLAYER_ID_NEUTRAL:
                        if delta != 0:
                            factory.owner = delta / abs(delta)
                    else:
                        factory.owner *= -1
                last_update = troop.time_left

    def add_future_command(self, src, dst, time_left):
        self.future_commands.append(Command(src, dst, time_left))
        self.update_perception_after_future_command(src, dst)

    def set_future_command(self, index, src, time_left):
        self.future_commands[index].src = src
        self.future_commands[index].time_left = time_left
        self.update_perception_after_future_command(src, self.future_commands[index].dst)

    def update_perception_after_future_command(self, src, dst):
        # Update perception as if we went through the full path already
        path = self.min_distances.get_cached_path(src, dst)
        cyborgs_needed = self.cyborgs_on_path(path, self.perceived_factories) + 1
        global turn
        for k in range(1, len(path)):
            dist = self.get_edge(path[k-1], path[k])
            next_factory = self.perceived_factories[path[k]]
            if self.perceived_factories[path[k-1]].num_cyborgs < cyborgs_needed:
                print("Error ({})! Not enough cyborgs perceived ({} < {}) at {}! Command({}, {}). Path: {}, Factories: {}"
                      .format(k, self.perceived_factories[path[k-1]].num_cyborgs, cyborgs_needed, path[k-1], src, dst, path, self.perceived_factories), file=sys.stderr)    # Throw error
                break
            if self.perceived_factories[path[k-1]].owner != PLAYER_ID_SELF:    # Throw error
                print("Error! Looking at factory ({}) that doesn't belong to me! Command({}, {}), Path: {}".format(path[k-1], src, dst, path), file=sys.stderr)
                break
            self.perceived_factories[path[k-1]].num_cyborgs -= cyborgs_needed   # first one should always be my factory

            if next_factory.owner == PLAYER_ID_SELF:
                next_factory.num_cyborgs += cyborgs_needed
            else:
                # Account for perceived generated cyborgs
                if next_factory.owner == PLAYER_ID_OPPONENT:
                    cyborgs_needed -= next_factory.cyborg_rate*(dist+1)
                cyborgs_lost = next_factory.num_cyborgs
                next_factory.num_cyborgs -= cyborgs_needed
                cyborgs_needed -= cyborgs_lost     # Take out battling cyborgs
                if next_factory.num_cyborgs < 0:
                    next_factory.owner = PLAYER_ID_SELF
                    next_factory.num_cyborgs *= -1      # make positive # cyborgs again
                else:
                    print("Error! num cyborgs ({}) at {} !< 0! Command({}, {}), Path: {}".format(next_factory.num_cyborgs, path[k], src, dst, path), file=sys.stderr)

    # Update all future commands
    def tick_commands(self):
        for cmd in self.future_commands:
            cmd.time_left -= 1

    # Remove None commands
    def prune_commands(self):
        self.future_commands = [cmd for cmd in self.future_commands if cmd]

    # Get all factories that a player owns
    def get_player_factories(self, player_id):
        if player_id in self.player_stats:
            return self.player_stats[player_id].factories
        return [factory_id for factory_id in self.factories if self.factories[factory_id].owner == PLAYER_ID_NEUTRAL]

    def get_sorted_factory_list(self):
        return sorted([factory for factory in self.factories if self.factories[factory].cyborg_rate != 0],
                      key=lambda x: self.factories[x].cyborg_rate, reverse=True)

    def get_target_factory_list(self, factories=None):
        if factories is None:
            factories = self.factories
        return [factory for factory in factories if factories[factory].cyborg_rate != 0
                and factories[factory].owner != PLAYER_ID_SELF]

    def get_compliment_filtered_list(self, factories=None):
        if factories is None:
            factories = self.factories
        return [factory for factory in factories if factories[factory].cyborg_rate == 0
                and factories[factory].owner != PLAYER_ID_SELF]

    def cyborgs_on_path(self, path, factories=None):
        if factories is None:
            factories = self.factories
        troops = 0
        dist = 0
        for k in range(1, len(path)):
            dist += self.get_edge(path[k-1], path[k])
            if factories[path[k]].owner == PLAYER_ID_SELF:
                # troops -= factories[path[k+1]].num_cyborgs
                # troops -= factories[path[k+1]].cyborg_rate*(dist+1)
                continue
            troops += factories[path[k]].num_cyborgs
            if factories[path[k]].owner == PLAYER_ID_OPPONENT:
                troops += factories[path[k]].cyborg_rate*(dist+1)
        return int(troops)

    def get_edge(self, u, v):
        return self.original_graph[u][v]

turn = 0


def init():
    factory_count = int(input())  # the number of factories
    link_count = int(input())  # the number of links between factories
    init_timer = timer.start()

    state = GameState(factory_count)
    msg_generator = MessageGenerator()

    for i in range(link_count):
        factory_1, factory_2, distance = [int(j) for j in input().split()]
        state.create_edge(factory_1, factory_2, distance)
        state.create_edge(factory_2, factory_1, distance)       # Undirected

    state.calculate_locality()
    state.min_distances.calculate()
    state.min_distances.cache_all_paths()

    d = timer.stop(init_timer)
    print("{:.2f} ms spent initializing".format(d.microseconds / 1000.0), file=sys.stderr)
    return state, msg_generator


def game_loop(state, msg_generator):
    loop_timer = timer.reserve_id()
    # game loop
    while True:
        global turn
        turn += 2   # for me and opponenet
        game_cmd = "MSG {}".format(msg_generator.get())

        state.next_round()

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
            # elif entity_type == "BOMB":
            #     print("BOMB", file=sys.stderr)

        timer.start(loop_timer)

        state.calculate_perception()
        state.tick_commands()

        # Check commands to execute
        for i in range(len(state.future_commands)):
            cmd = state.future_commands[i]
            path = state.min_distances.get_cached_path(cmd.src, cmd.dst)
            cyborgs_needed = state.cyborgs_on_path(path, state.perceived_factories) + 1
            if cmd.time_left < 0:
                if state.factories[cmd.src].owner == PLAYER_ID_OPPONENT:
                    state.future_commands[i] = None
                    continue
                if state.factories[cmd.src].num_cyborgs >= cyborgs_needed:
                    game_cmd += ";{} {} {} {}".format(CMD_MOVE, cmd.src, path[1], cyborgs_needed)
                    state.update_after_move(cmd.src, path[1], cyborgs_needed)
                    if len(path) > 2:
                        state.set_future_command(i, path[1], state.get_edge(cmd.src, path[1]))
                    else:
                        state.future_commands[i] = None
                else:
                    state.future_commands[i] = None
            else:
                if state.perceived_factories[cmd.src].num_cyborgs >= cyborgs_needed:
                    # update perception map
                    print("", file=sys.stderr)

        state.prune_commands()

        my_factories = state.get_player_factories(PLAYER_ID_SELF)
        print("My factories: {}".format(my_factories), file=sys.stderr)
        if not my_factories:
            print("WAIT")
            continue

        ################################################################################
        my_factories.sort(key=lambda x: state.factories[x].locality)
        mean_locality = sum([state.factories[f].locality for f in my_factories]) / float(len(my_factories))

        for i in range(len(my_factories)):
            filtered_list = state.get_target_factory_list(state.perceived_factories)
            if not filtered_list:
                filtered_list = state.get_compliment_filtered_list(state.perceived_factories)

            # Get the real factory
            factory = state.factories[my_factories[i]]

            # Don't move from here if we're not perceived to own it
            if state.perceived_factories[factory.id].owner != PLAYER_ID_SELF:
                continue

            # Find the closest targets
            closest = math.inf
            target_id = -1
            num_cyborgs = 0
            for factory_id in filtered_list:
                rate = state.perceived_factories[factory_id].cyborg_rate
                dist = state.min_distances.get_distance(factory.id, factory_id)
                path = state.min_distances.get_cached_path(factory.id, factory_id)
                cyborgs_needed = state.cyborgs_on_path(path, state.perceived_factories) + 1
                if rate != 0:
                    weighted_dist = dist / float(rate)
                # Don't move if we're going to lose it
                if cyborgs_needed <= state.perceived_factories[factory.id].num_cyborgs:
                    if weighted_dist < closest:
                        target_id = factory_id
                        closest = weighted_dist
                        num_cyborgs = cyborgs_needed
            if target_id != -1:
                path = state.min_distances.get_cached_path(u=factory.id, v=target_id)
                if len(path) < 2:
                    print("Path ({},{}) too short! {}".format(factory.id, target_id, path), file=sys.stderr)
                else:
                    game_cmd += ";MOVE {} {} {}".format(factory.id, path[1], num_cyborgs)
                    state.update_after_move(factory.id, path[1], num_cyborgs)
                    if len(path) > 2:
                        state.add_future_command(src=path[1],
                                                 dst=target_id,
                                                 time_left=state.get_edge(factory.id, path[1]))
            # elif i > 0 and factory.locality > mean_locality:
            #     num_cyborgs = int(state.perceived_factories[factory.id].num_cyborgs / 2)
            #     next_factory = int(i / 2)
            #     if num_cyborgs > 0:
            #         path = state.min_distances.get_cached_path(u=factory.id, v=my_factories[next_factory])
            #         if len(path) < 2:
            #             print("2Path ({},{}) too short! {}".format(factory.id, my_factories[next_factory], path), file=sys.stderr)
            #         else:
            #             game_cmd += ";MOVE {} {} {}".format(factory.id, path[1], num_cyborgs)
            #             state.update_after_move(factory.id, path[1], num_cyborgs)
            #             if len(path) > 2:
            #                 state.add_future_command(src=path[1],
            #                                          dst=my_factories[next_factory],
            #                                          time_left=state.get_edge(factory.id, path[1]))

        # source_factory_id = my_factories[0].id # max(my_factories, key=lambda x: state.factories[x].num_cyborgs)
        # target_factory_id = -1
        # num_cyborgs = 0
        # source_factory = state.factories[source_factory_id]
        # closest_dist = math.inf
        #
        # for factory in filtered_list:
        #     rate = state.factories[factory].cyborg_rate
        #     distance = state.min_distances.get_distance(source_factory_id, factory)
        #     path = state.min_distances.get_cached_path(source_factory_id, factory)
        #     cyborgs_needed = state.cyborgs_on_path(path, state.perceived_factories) + 1
        #     if rate != 0:
        #         weighted_dist = distance / float(rate)
        #     if cyborgs_needed <= source_factory.num_cyborgs:
        #         if weighted_dist < closest_dist:
        #             target_factory_id = factory
        #             closest_dist = weighted_dist
        #             num_cyborgs = cyborgs_needed
        # if target_factory_id == -1:
        #     game_cmd += ";WAIT"
        # elif num_cyborgs <= 0:
        #     path = state.min_distances.get_cached_path(u=source_factory_id, v=target_factory_id)
        #     if len(path) > 2:
        #         state.add_future_command(src=path[1], dst=target_factory_id, time_left=1)
        # else:
        #     path = state.min_distances.get_cached_path(u=source_factory_id, v=target_factory_id)
        #     if len(path) < 2:
        #         print("Path ({},{}) too short! {}".format(source_factory_id, target_factory_id, path), file=sys.stderr)
        #     else:
        #         game_cmd += ";MOVE {} {} {}".format(source_factory_id, path[1], num_cyborgs)
        #         state.update_after_move(source_factory_id, path[1], num_cyborgs)
        #         if len(path) > 2:
        #             state.add_future_command(src=path[1],
        #                                      dst=target_factory_id,
        #                                      time_left=state.get_edge(source_factory_id, path[1]))

        print(game_cmd)
        d = timer.delta(loop_timer)
        print("{:.2f} ms spent on turn {}".format(d.microseconds / 1000.0, turn), file=sys.stderr)


def main():
    state, msg_generator = init()
    game_loop(state, msg_generator)

main()
