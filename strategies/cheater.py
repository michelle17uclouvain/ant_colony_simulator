from environment import TerrainType
from ant import AntAction, AntStrategy
from common import AntPerception, Direction

import math
import random
from collections import deque


class CheaterStrategy(AntStrategy):
    """
    Cheater strategy with full access to the Environment object.
    Uses BFS pathfinding on the complete grid to navigate optimally.
    Deposits pheromones to help non-cheater ants.

    Implemented with the help of Claude (claude.ai).
    Prompt: "Implement a cheater ant strategy that uses BFS pathfinding with access
    to the full environment. It must implement set_environment(), use env.food_positions
    and env.colony_positions, locate itself via env.ants and ant_id, and deposit
    pheromones to guide other ants."
    """

    def __init__(self):
        self.env = None
        self._paths  = {}       # ant_id -> deque of (x, y) remaining waypoints
        self._goals  = {}       # ant_id -> (x, y) fixed target until invalidated
        self._ant_lookup = {}   # ant_id -> Ant (lazy cache)

    def set_environment(self, environment) -> None:
        self.env = environment

    # ------------------------------------------------------------------ #

    def decide_action(self, perception: AntPerception) -> AntAction:
        if self.env is None:
            return AntAction.NO_ACTION

        ant = self._find_ant(perception.ant_id)
        if ant is None:
            return AntAction.NO_ACTION

        ax, ay = int(ant.x), int(ant.y)

        if perception.has_food:
            return self._return_to_colony(perception, ant, ax, ay)
        else:
            return self._go_to_food(perception, ant, ax, ay)

    # ------------------------------------------------------------------ #

    def _return_to_colony(self, perception, ant, ax, ay):
        if self.env.get_terrain(ax, ay) == TerrainType.COLONY:
            self._clear_path(ant.id)
            return AntAction.DROP_FOOD

        # Deposit food pheromone to guide explorer ants toward food
        if random.random() < 0.4:
            return AntAction.DEPOSIT_FOOD_PHEROMONE

        target = self._nearest_colony_cell()
        if target is None:
            return AntAction.NO_ACTION
        return self._follow_path(ant, ax, ay, target, fixed=True)

    def _go_to_food(self, perception, ant, ax, ay):
        if self.env.get_terrain(ax, ay) == TerrainType.FOOD:
            self._clear_path(ant.id)
            return AntAction.PICK_UP_FOOD

        # Deposit home pheromone to help returning food-carriers find colony
        if random.random() < 0.4:
            return AntAction.DEPOSIT_HOME_PHEROMONE

        if not self.env.food_positions:
            return AntAction.NO_ACTION

        return self._follow_path_to_food(ant, ax, ay)

    # ------------------------------------------------------------------ #

    def _follow_path_to_food(self, ant, ax, ay) -> AntAction:
        cached_goal = self._goals.get(ant.id)

        # Invalidate if the target food cell is now empty
        if cached_goal is not None and cached_goal not in self.env.food_positions:
            self._clear_path(ant.id)
            cached_goal = None

        # Choose a new target (fixed until consumed)
        if cached_goal is None:
            cached_goal = self._nearest_food(ax, ay)
            if cached_goal is None:
                return AntAction.NO_ACTION
            self._goals[ant.id] = cached_goal
            self._paths.pop(ant.id, None)

        return self._follow_path(ant, ax, ay, cached_goal, fixed=True)

    def _follow_path(self, ant, ax, ay, target, fixed=False) -> AntAction:
        cached_path = self._paths.get(ant.id)

        if not cached_path:
            path = self._bfs(ax, ay, target)
            if path is None or len(path) < 2:
                self._clear_path(ant.id)
                return AntAction.NO_ACTION
            self._paths[ant.id] = deque(path)
            cached_path = self._paths[ant.id]

        # Advance past waypoints already reached
        while cached_path and cached_path[0] == (ax, ay):
            cached_path.popleft()

        if not cached_path:
            self._clear_path(ant.id)
            return AntAction.NO_ACTION

        nx, ny = cached_path[0]
        return self._step_towards(ant, nx, ny)

    def _step_towards(self, ant, tx, ty) -> AntAction:
        ax, ay = int(ant.x), int(ant.y)
        dx, dy = tx - ax, ty - ay
        if dx == 0 and dy == 0:
            return AntAction.MOVE_FORWARD

        target_dir = self._dir_from_delta(dx, dy)
        diff = (target_dir - ant.direction.value) % 8
        if diff == 0:
            return AntAction.MOVE_FORWARD
        elif diff <= 4:
            return AntAction.TURN_RIGHT
        else:
            return AntAction.TURN_LEFT

    # ------------------------------------------------------------------ #

    def _bfs(self, sx, sy, goal):
        gx, gy = goal
        if (sx, sy) == (gx, gy):
            return [(sx, sy)]

        parent = {(sx, sy): None}
        queue = deque([(sx, sy)])

        while queue:
            x, y = queue.popleft()
            for ddx, ddy in [(0, -1), (0, 1), (-1, 0), (1, 0),
                              (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nx, ny = x + ddx, y + ddy
                if (nx, ny) in parent or not self.env.is_walkable(nx, ny):
                    continue
                parent[(nx, ny)] = (x, y)
                if nx == gx and ny == gy:
                    path = []
                    node = (nx, ny)
                    while node is not None:
                        path.append(node)
                        node = parent[node]
                    path.reverse()
                    return path
                queue.append((nx, ny))
        return None

    def _nearest_food(self, ax, ay):
        if not self.env.food_positions:
            return None
        return min(self.env.food_positions,
                   key=lambda p: (abs(p[0] - ax) + abs(p[1] - ay), p[0], p[1]))

    def _nearest_colony_cell(self):
        if not self.env.colony_positions:
            return None
        return self.env.colony_positions[0]

    def _clear_path(self, ant_id):
        self._paths.pop(ant_id, None)
        self._goals.pop(ant_id, None)

    def _find_ant(self, ant_id):
        ant = self._ant_lookup.get(ant_id)
        if ant is None:
            for a in self.env.ants:
                self._ant_lookup[a.id] = a
            ant = self._ant_lookup.get(ant_id)
        return ant

    def _dir_from_delta(self, dx, dy) -> int:
        if dx == 0 and dy == 0:
            return Direction.NORTH.value
        return int(((math.atan2(dy, dx) + math.pi / 2) * 4 / math.pi + 0.5) % 8) % 8
