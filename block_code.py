from copy import deepcopy

from actions import BlocksAction

def goal_from_state(state: tuple[int, list[list[int]]]) -> tuple[int, list[list[int]]]:
    return (None, 
            [sorted(
                sum(state[1], []) + ([] if state[0] is None else [state[0]]), 
                reverse = True
            )]
        )

def int_to_char(my_int: int) -> str:
    """Takes an int 0...25 and returns the corresponding lower case char"""
    if not -1 < my_int < 26:
        raise ValueError(f'int out of bounds: {my_int}')
    
    return chr(my_int + ord('a'))

def int_state_to_char(state: tuple[int, list[list[int]]]) -> tuple[str, list[list[str]]]:
    """Turns a state of ints into a state of chars 0...n -> a...z"""
    return [None if state[0] is None else int_to_char(state[0]), [[int_to_char(block) for block in stack] for stack in state[1]]]

def char_to_int(my_char: str) -> int:
    """Takes an char a...z and returns the corresponding int"""
    my_char = my_char.lower()
    if not len(my_char) == 1 and ord('a') <= ord(my_char) <= ord('z'):
        raise ValueError(f'Invalid char: {my_char}')
    
    return ord(my_char) - ord('a')

def char_state_to_int(state: tuple[str, list[list[str]]]) -> tuple[int, list[list[int]]]:
    """Turns a state of ints into a state of chars a...z -> 0...n"""
    return [None if state[0] is None else char_to_int(state[0]), [[char_to_int(block) for block in stack] for stack in state[1]]]

def state_to_pddl(state: tuple[str | int, list[list[str | int]]], is_goal = False) -> list[str]:
    """
    Turns char or int BlocksWorld state into pddl form (list of strings, with brackets). 
    `is_goal` turns the state into a partial goal state (instead of a complete state decription)
    """
    pddl = {
        'holding' : [] if (state[0] is None or is_goal) else [str(state[0])],
        'clear' : [],
        'on' : [],
        'ontable' : []
    }
    for stack in state[1]:
        if not is_goal:
            pddl['clear'].append(str(stack[-1]))
            pddl['ontable'].append(str(stack[0]))
        pddl['on'] += [f'{x} {y}' for x, y in zip(stack[1:], stack[:-1])][::-1]
    
    return (['(handempty)'] if (state[0] is None and not is_goal) else []) + sum([[f'({key} {objects})' for objects in pddl[key]] for key in pddl.keys()], [])

def apply_action(action: str, state: tuple[str | int, list[list[str | int]]]) -> tuple[bool, tuple[str | int, list[list[str | int]]]]:
    """Applies action out of place. Works for int or str states.
    
    Returns
        - **(True, new_state)** if action is possible.
        - **(False, old_state)** otherwise
    """
    try:
        tokens = action[1:-1].split()
        action_list = [int(block) if block.isnumeric() else block for block in tokens[1:]]
        action_tag = tokens[0]
    except IndexError:
        return False, state
    
    ActionClass = next((ac for ac in BlocksAction.get_actions() if ac.get_name() == action_tag), None)

    try:
        action: BlocksAction = ActionClass(action_list)
    except (TypeError, ValueError):
        return False, state

    if action.meets_preconditions(state):
        return (True, action.apply_to_state(state))
    else:
        return False, state
            
def test_plan(plan: list[str], state: tuple[str | int, list[list[str | int]]]) -> dict:
    """
    **plan** is list of `(action object object ...)` strings
    
    **state** is `tuple[str | int, list[list[str | int]]]`

    Returns dict:
        - `result`
            - SUCCESS if plan reaches goal successfully.
            - NOTGOAL if the plan is executable but does not reach a goal state
            - NOTEXECUTABLE if the plan is not executable
        - `last_action` is the last action evaluated.
        - `final_state` is the final state after running the plan until the first non-exec action.
    """
    def to_dict(result: str, last_action: str, final_state: tuple[str | int, list[list[str | int]]]) -> dict:
        return {
            'result' : result,
            'last_action' : last_action,
            'final_state' : final_state
        }

    current_state = deepcopy(state)
    goal = goal_from_state(state)

    for action in plan:
        check, current_state = apply_action(action, current_state)
        if not check:
            return to_dict('NOTEXECUTABLE', action, current_state)
        if current_state == goal:
            return to_dict('SUCCESS', action, current_state)
    else:
        return to_dict('NOTGOAL', action, current_state)
                       