from environment import TerrainType, AntPerception
from ant import AntAction, AntStrategy
from common import Direction

import random
import math

class CooperativeStrategy(AntStrategy):
    """
    # TODO: Insert your code here
    """

    shared_food_hints = {} 
    HINT_TTL = 220

    ALPHA = 1.2
    BETA = 1.8
    EXPLORE_RATE = 0.08
    PHEROMONE_INFLUENCE_EPS = 1e-6

    def __init__(self):
        """Initialize the strategy with last action tracking"""
        # TODO: Insert your code here
        self.ant_memory = {}

    def decide_action(self, perception: AntPerception) -> AntAction:
        """Decide an action based on current perception"""

        # TODO: Insert your code here

        state = self.ant_memory.setdefault(
            perception.ant_id,
            {
                "colony_memory": None,
                "food_memory": [],
                "last_action": None,
                "last_forward_clear": False,
                "stuck": 0,
                "step": 0,
            },
        )
        state["step"] += 1

        if CooperativeStrategy.shared_food_hints and random.random() <= 0.15:
            dead = []
            for rel in list(CooperativeStrategy.shared_food_hints.keys()):
                CooperativeStrategy.shared_food_hints[rel] -= 1
                if CooperativeStrategy.shared_food_hints[rel] <= 0:
                    dead.append(rel)
            for rel in dead:
                del CooperativeStrategy.shared_food_hints[rel]

        if state["last_action"] == AntAction.MOVE_FORWARD and state["last_forward_clear"]:
            ddx, ddy = Direction.get_delta(perception.direction)
            if state["colony_memory"] is not None:
                state["colony_memory"] = (
                    state["colony_memory"][0] - ddx,
                    state["colony_memory"][1] - ddy,
                )
            state["food_memory"] = [
                (fx - ddx, fy - ddy) for fx, fy in state["food_memory"]
            ]

        colony_cell = self._closest_cell(perception, TerrainType.COLONY)
        if colony_cell is not None:
            state["colony_memory"] = colony_cell

        for (dx, dy), terrain in perception.visible_cells.items():
            if terrain == TerrainType.FOOD and (dx, dy) not in state["food_memory"]:
                state["food_memory"].append((dx, dy))

        colony_cell = self._closest_cell(perception, TerrainType.COLONY)
        if colony_cell is not None:
            cx, cy = colony_cell
            for (dx, dy), terrain in perception.visible_cells.items():
                if terrain == TerrainType.FOOD:
                    rel = (dx - cx, dy - cy)
                    CooperativeStrategy.shared_food_hints[rel] = CooperativeStrategy.HINT_TTL

        if perception.has_food and perception.visible_cells.get((0, 0)) == TerrainType.COLONY:
            return AntAction.DROP_FOOD

        if not perception.has_food and perception.visible_cells.get((0, 0)) == TerrainType.FOOD:
            return AntAction.PICK_UP_FOOD

        if perception.has_food and state["step"] % 100 == 0:
            return AntAction.DEPOSIT_FOOD_PHEROMONE
        if not perception.has_food and state["step"] % 200 == 0:
            return AntAction.DEPOSIT_HOME_PHEROMONE

        return self._decide_movement(perception)

    def _decide_movement(self, perception: AntPerception) -> AntAction:
        """Decide which direction to move based on current state"""
        # TODO: Insert your code here

        state = self.ant_memory.setdefault(
            perception.ant_id,
            {
                "colony_memory": None,
                "food_memory": [],
                "last_action": None,
                "last_forward_clear": False,
                "stuck": 0,
                "step": 0,
            },
        )

        if perception.has_food:
            if perception.can_see_colony():
                return self._move_towards(perception, perception.get_colony_direction(), state)

            if state["colony_memory"] is not None:
                if math.hypot(*state["colony_memory"]) < 2:
                    state["colony_memory"] = None
                else:
                    return self._move_towards(perception, self._direction_from_delta(state["colony_memory"]), state)

            return self._wander(perception, state)

        if perception.can_see_food():
            return self._move_towards(perception, perception.get_food_direction(), state)

        colony_cell = self._closest_cell(perception, TerrainType.COLONY)
        if colony_cell is not None and CooperativeStrategy.shared_food_hints:
            top = sorted(CooperativeStrategy.shared_food_hints.items(), key=lambda x: x[1], reverse=True)[:3]
            if top:
                hint = random.choice(top)[0]
                cx, cy = colony_cell
                return self._move_towards(perception, self._direction_from_delta((cx + hint[0], cy + hint[1])), state)

        if state["food_memory"]:
            target = state["food_memory"][0]
            if math.hypot(*target) < 1.5:
                state["food_memory"].pop(0)
            else:
                return self._move_towards(perception, self._direction_from_delta(target), state)

        food_scores = {d.value: 0.0 for d in Direction}
        for (dx, dy), amount in perception.food_pheromone.items():
            if amount <= 0:
                continue
            d = self._direction_from_delta((dx, dy))
            dist = max(1.0, math.hypot(dx, dy))
            food_scores[d] += amount / dist
        best_food_dir = max(food_scores, key=lambda k: food_scores[k])
        food_dir = best_food_dir if food_scores[best_food_dir] > 0 else None
        if food_dir is not None:
            return self._move_towards(perception, food_dir, state)

        return self._wander(perception, state)

# -------------------------------------------------------------------------------------------- helpers

    # ant scans what it sees for a a type of terrain
    def _closest_cell(self, perception: AntPerception, terrain: TerrainType):
        best = None
        best_dist = float("inf")
        for (dx, dy), t in perception.visible_cells.items():
            if t == terrain:
                d = math.hypot(dx, dy)
                if d < best_dist:
                    best_dist = d
                    best = (dx, dy)
        return best

    # ant tries to move towards a target direction and will wander if no cues are seen
    def _move_towards(self, perception: AntPerception, target_dir, state: dict) -> AntAction:
        if target_dir is None:
            return self._wander(perception, state)

        target_val = target_dir.value if isinstance(target_dir, Direction) else target_dir
        diff = (target_val - perception.direction.value) % 8

        if diff == 0:
            action = AntAction.MOVE_FORWARD
            dx, dy = Direction.get_delta(perception.direction)
            state["last_forward_clear"] = perception.visible_cells.get((dx, dy)) not in (TerrainType.WALL, None)
        else:
            cur = perception.direction.value
            left_dir = (cur - 1) % 8
            right_dir = (cur + 1) % 8
            use_food = perception.has_food

            left_score = 0.0
            right_score = 0.0
            pher_map = perception.food_pheromone if use_food else perception.home_pheromone
            for (dx, dy), amount in pher_map.items():
                if amount <= 0:
                    continue
                d = math.hypot(dx, dy)
                dir_idx = self._direction_from_delta((dx, dy))
                if dir_idx == left_dir:
                    left_score += amount / max(1.0, d)
                elif dir_idx == right_dir:
                    right_score += amount / max(1.0, d)
            # slight randomness to avoid premature convergence
            if random.random() < 0.08:
                choose_left = random.choice([True, False])
            else:
                choose_left = left_score >= right_score

            if diff == 4 and random.random() < 0.5:
                action = AntAction.TURN_LEFT
            else:
                if choose_left:
                    action = AntAction.TURN_LEFT
                else:
                    action = AntAction.TURN_RIGHT
            state["last_forward_clear"] = False

        state["last_action"] = action
        return action
    
    # ant moves randomly to avoid getting stuck in one place (with a small chance of exploring instead of following pheromone cues)
    def _wander(self, perception: AntPerception, state: dict) -> AntAction:
        cur = perception.direction.value
        forward_dir = cur
        left_dir = (cur - 1) % 8
        right_dir = (cur + 1) % 8

        use_food = perception.has_food
        f_score = l_score = r_score = 0.0
        pher_map = perception.food_pheromone if use_food else perception.home_pheromone
        for (dx, dy), amount in pher_map.items():
            if amount <= 0:
                continue
            dist = math.hypot(dx, dy)
            dir_idx = self._direction_from_delta((dx, dy))
            if dir_idx == forward_dir:
                f_score += amount / max(1.0, dist)
            elif dir_idx == left_dir:
                l_score += amount / max(1.0, dist)
            elif dir_idx == right_dir:
                r_score += amount / max(1.0, dist)

        f_weight = ((f_score + self.PHEROMONE_INFLUENCE_EPS) ** self.ALPHA) * (1.3 ** self.BETA)
        l_weight = ((l_score + self.PHEROMONE_INFLUENCE_EPS) ** self.ALPHA) * (1.0 ** self.BETA)
        r_weight = ((r_score + self.PHEROMONE_INFLUENCE_EPS) ** self.ALPHA) * (1.0 ** self.BETA)

        dx, dy = Direction.get_delta(perception.direction)
        forward_blocked = perception.visible_cells.get((dx, dy)) in (TerrainType.WALL, None)
        if forward_blocked:
            f_weight *= 0.01

        if random.random() < self.EXPLORE_RATE:
            probs = [1.0, 1.0, 1.0]
        else:
            probs = [f_weight, l_weight, r_weight]

        total = sum(probs)
        if total <= 0:
            probs = [1.0, 1.0, 1.0]
            total = 3.0

        probs = [p / total for p in probs]
        choice = random.choices([0, 1, 2], weights=probs)[0]

        if choice == 0:
            state["stuck"] = 0
            action = AntAction.MOVE_FORWARD
            state["last_forward_clear"] = True
        else:
            state["stuck"] += 1
            action = AntAction.TURN_LEFT if choice == 1 else AntAction.TURN_RIGHT
            state["last_forward_clear"] = False

        state["last_action"] = action
        return action
    
    # 8 direction mapping, to convert a tile into an index
    def _direction_from_delta(self, pos: tuple) -> int:
        dx, dy = pos
        if dx == 0 and dy == 0:
            return Direction.NORTH.value
        return int((math.atan2(dy, dx) / (2 * math.pi) * 8 + 2.5)) % 8