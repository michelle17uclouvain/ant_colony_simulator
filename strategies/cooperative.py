from environment import TerrainType, AntPerception
from ant import AntAction, AntStrategy
from common import Direction

import random
import math


class CooperativeStrategy(AntStrategy):

    def __init__(self):
        self.last_action = None
        self.last_forward_was_clear = False
        self.stuck_counter = 0

    def decide_action(self, perception: AntPerception) -> AntAction:
        if perception.has_food:
            return self._return_to_colony(perception)
        else:
            return self._search_for_food(perception)

    # ------------------------------------------------------------------ #

    def _return_to_colony(self, perception: AntPerception) -> AntAction:
        # Drop food if standing on colony
        if perception.visible_cells.get((0, 0)) == TerrainType.COLONY:
            return AntAction.DROP_FOOD

        # Deposit food pheromone occasionally to guide other ants toward food
        if self.last_action == AntAction.MOVE_FORWARD and self.last_forward_was_clear and random.random() < 0.35:
            self.last_action = AntAction.DEPOSIT_FOOD_PHEROMONE
            return AntAction.DEPOSIT_FOOD_PHEROMONE

        # Head toward colony if visible
        if perception.can_see_colony():
            return self._go(perception, perception.get_colony_direction())

        # Follow home pheromone trail toward colony
        best_dir = self._best_home_pheromone_dir(perception)
        if best_dir is not None:
            return self._go(perception, best_dir)

        return self._random_walk(perception)

    def _search_for_food(self, perception: AntPerception) -> AntAction:
        # Pick up food if standing on it
        if perception.visible_cells.get((0, 0)) == TerrainType.FOOD:
            return AntAction.PICK_UP_FOOD

        # Deposit home pheromone occasionally to help food-carrying ants return
        if self.last_action == AntAction.MOVE_FORWARD and self.last_forward_was_clear and random.random() < 0.35:
            self.last_action = AntAction.DEPOSIT_HOME_PHEROMONE
            return AntAction.DEPOSIT_HOME_PHEROMONE

        # Move toward visible food
        if perception.can_see_food():
            return self._go(perception, perception.get_food_direction())

        # Follow food pheromone trail
        best_dir = self._best_food_pheromone_dir(perception)
        if best_dir is not None:
            return self._go(perception, best_dir)

        return self._random_walk(perception)

    # ------------------------------------------------------------------ #

    def _best_food_pheromone_dir(self, perception: AntPerception):
        best_dir = None
        best_score = 0.0
        for (dx, dy), amount in perception.food_pheromone.items():
            if amount > best_score:
                best_score = amount
                best_dir = self._dir_to((dx, dy))
        return best_dir

    def _best_home_pheromone_dir(self, perception: AntPerception):
        best_dir = None
        best_score = 0.0
        for (dx, dy), amount in perception.home_pheromone.items():
            if amount > best_score:
                best_score = amount
                best_dir = self._dir_to((dx, dy))
        return best_dir

    def _go(self, perception: AntPerception, target_dir) -> AntAction:
        if target_dir is None:
            return self._random_walk(perception)
        target_val = target_dir.value if isinstance(target_dir, Direction) else target_dir
        diff = (target_val - perception.direction.value) % 8
        if diff == 0:
            action = AntAction.MOVE_FORWARD
            dx, dy = Direction.get_delta(perception.direction)
            self.last_forward_was_clear = perception.visible_cells.get((dx, dy)) not in (TerrainType.WALL, None)
        else:
            action = AntAction.TURN_RIGHT if diff <= 4 else AntAction.TURN_LEFT
            self.last_forward_was_clear = False
        self.last_action = action
        return action

    def _random_walk(self, perception: AntPerception) -> AntAction:
        dx, dy = Direction.get_delta(perception.direction)
        blocked = perception.visible_cells.get((dx, dy)) == TerrainType.WALL
        crowded = len(perception.nearby_ants) >= 3

        if blocked:
            self.stuck_counter += 1
            action = AntAction.TURN_LEFT if self.stuck_counter % 2 == 0 else AntAction.TURN_RIGHT
            self.last_forward_was_clear = False
        elif crowded:
            action = random.choice([AntAction.TURN_LEFT, AntAction.TURN_RIGHT])
            self.stuck_counter = 0
            self.last_forward_was_clear = False
        else:
            self.stuck_counter = 0
            action = random.choices(
                [AntAction.MOVE_FORWARD, AntAction.TURN_LEFT, AntAction.TURN_RIGHT],
                weights=[0.65, 0.175, 0.175]
            )[0]
            self.last_forward_was_clear = (action == AntAction.MOVE_FORWARD)

        self.last_action = action
        return action

    def _dir_to(self, pos: tuple) -> int:
        dx, dy = pos
        if dx == 0 and dy == 0:
            return Direction.NORTH.value
        return int(((math.atan2(dy, dx) + math.pi / 2) * 4 / math.pi + 0.5) % 8) % 8
