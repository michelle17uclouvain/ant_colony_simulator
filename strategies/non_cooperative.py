from environment import TerrainType, AntPerception
from ant import AntAction, AntStrategy
from common import Direction

import random
import math


class NonCooperativeStrategy(AntStrategy):
    """
    Non-cooperative ant strategy using individual memory.
    Each ant maintains a local map of colony and food positions
    """

    def __init__(self):
        self.colony_memory = None  # relative (dx, dy) to colony from ant's current position
        self.food_memory = []      # list of relative (dx, dy) to known food spots
        self.last_action = None
        self.last_forward_was_clear = False  # whether the last MOVE_FORWARD was unobstructed
        self.stuck_counter = 0

    def decide_action(self, perception: AntPerception) -> AntAction:
        self._update_memory(perception)

        if perception.has_food:
            return self._return_to_colony(perception)

        if perception.visible_cells.get((0, 0)) == TerrainType.FOOD:
            return AntAction.PICK_UP_FOOD

        if perception.can_see_food():
            return self._go(perception, perception.get_food_direction())

        return self._explore(perception)

    def _update_memory(self, perception: AntPerception):
        """Update relative positions of colony and food after each move."""
        # Only shift stored positions if the last MOVE_FORWARD actually succeeded
        if self.last_action == AntAction.MOVE_FORWARD and self.last_forward_was_clear:
            ddx, ddy = Direction.get_delta(perception.direction)
            if self.colony_memory:
                self.colony_memory = (self.colony_memory[0] - ddx, self.colony_memory[1] - ddy)
            self.food_memory = [(fx - ddx, fy - ddy) for fx, fy in self.food_memory]

        # Update memory from current perception
        for (dx, dy), terrain in perception.visible_cells.items():
            if terrain == TerrainType.COLONY:
                self.colony_memory = (dx, dy)
            if terrain == TerrainType.FOOD and (dx, dy) not in self.food_memory:
                self.food_memory.append((dx, dy))

    def _return_to_colony(self, perception: AntPerception) -> AntAction:
        if perception.visible_cells.get((0, 0)) == TerrainType.COLONY:
            return AntAction.DROP_FOOD
        if perception.can_see_colony():
            return self._go(perception, perception.get_colony_direction())
        if self.colony_memory:
            dist = math.hypot(*self.colony_memory)
            # Memory has drifted: we're "at" the colony but can't see it so we reset and search
            if dist < 2:
                self.colony_memory = None
                return self._random_walk(perception)
            return self._go(perception, self._dir_to(self.colony_memory))
        return self._random_walk(perception)

    def _explore(self, perception: AntPerception) -> AntAction:
        if self.food_memory:
            target = self.food_memory[0]
            if math.hypot(*target) < 1.5:
                self.food_memory.pop(0)
            else:
                return self._go(perception, self._dir_to(target))
        return self._random_walk(perception)

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
        if blocked:
            self.stuck_counter += 1
            action = AntAction.TURN_LEFT if self.stuck_counter % 2 == 0 else AntAction.TURN_RIGHT
            self.last_forward_was_clear = False
        else:
            self.stuck_counter = 0
            action = random.choices(
                [AntAction.MOVE_FORWARD, AntAction.TURN_LEFT, AntAction.TURN_RIGHT],
                weights=[0.6, 0.2, 0.2]
            )[0]
            self.last_forward_was_clear = (action == AntAction.MOVE_FORWARD)
        self.last_action = action
        return action

    def _dir_to(self, pos: tuple) -> int:
        """Convert a relative (dx, dy) position to a Direction index."""
        dx, dy = pos
        if dx == 0 and dy == 0:
            return Direction.NORTH.value
        return int((math.atan2(dy, dx) / (2 * math.pi) * 8 + 2.5)) % 8
