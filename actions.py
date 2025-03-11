from typing import Callable, Union
from abc import ABC, abstractmethod
from copy import deepcopy

def find_block(block: str, stacks: list[list[str | int]]) -> int | None:
    """Returns a index of the stack that the block is in OR None"""
    return next((i for (i, stack) in enumerate(stacks) if block in stack), None)

# setup actions
class BlocksAction(ABC):
    @staticmethod
    def get_actions() -> list["BlocksAction"]:
        """Returns the four BlocksWorld action classes in a list"""
        return [
            PickupAction, 
            PutdownAction, 
            StackAction, 
            UnstackAction
        ]

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        raise NotImplementedError()
    
    @staticmethod
    @abstractmethod
    def get_num_objects() -> int:
        """Get number of objects that this action should take."""
        raise NotImplementedError()
    
    @classmethod
    def _get_object_selection_functions(cls) -> list[Callable[[tuple[str | int, list[list[str | int]]]], list[str | int]]]:
        """Returns `num_object` functions which map states to suggested objects at each position"""
        return [lambda state: sum(state[1], []) + ([] if state[0] is None else [state[0]]) for _ in range(cls.get_num_objects())]
    
    @classmethod
    def get_suggested_objects(cls, state: tuple[str | int, list[list[str | int]]]) -> list[list[str | int]]:
        """Returns a `num_object`-length list of objects recommended for each object position. 
        Serves to speed up the action-generation in my code.
        In high-level planners this step usually is not needed.
        """
        return [func(state) for func in cls._get_object_selection_functions()]
    
    def __init__(self, objects: list[str | int]) -> None:
        if not len(objects) == self.get_num_objects():
            raise ValueError(f'Incorrect number of objects ({len(objects)}) for {self.get_name()}: {objects} (Expected {self.get_num_objects()})')
        self.objects = objects
    
    @abstractmethod
    def meets_preconditions(self, state: tuple[str | int, list[list[str | int]]]) -> bool:
        """Takes an action `(action_tag, [objects])` and a state `[holding, [stacks]]` 

        Returns 
            - **True** if the action can be applied.
            - **False** otherwise
        """
        raise NotImplementedError()

    
    def apply_to_state(self, state: tuple[str | int, list[list[str | int]]]) -> tuple[str | int, list[list[str | int]]]:
        """Takes an action `(action_tag, [objects])` to state `[holding, [stacks]]` out of place.
        
        Returns new state `[holding, [stacks]]`

        Assumes that `meets_preconditions` has been called, so no checks (for performance).
        """
        new_state = [state[0], deepcopy(state[1])]
        self._apply_in_place(new_state)
        return tuple(new_state) # this is a bit weird, but it lets me keep the tuple form without significant changes to how I wrote the other code.
    
    @abstractmethod
    def _apply_in_place(self, state: tuple[str | int, list[list[str | int]]]) -> None:
        """Applies the action in place, inner method."""
        raise NotImplementedError()
    
    def __str__(self) -> str:
        return f'({self.get_name()} {" ".join([str(o) for o in self.objects])})'
    
    def __eq__(self, other: Union["BlocksAction", str]) -> bool:
        if isinstance(other, BlocksAction):
            return self.__str__() == other.__str__()
        elif isinstance(other, str):
            return self.__str__() == other
        else:
            raise ValueError(f'Cannot compare {type(other)} to BlocksAction')

class PickupAction(BlocksAction):
    @staticmethod
    def get_name() -> str:
        return 'pickup'

    @staticmethod
    def get_num_objects() -> int:
        return 1
    
    @classmethod
    def _get_object_selection_functions(cls) -> list[Callable[[tuple[str | int, list[list[str | int]]]], list[str | int]]]:
        return [
            lambda state: [stack[-1] for stack in state[1]] # can only pickup the top block
        ]

    def meets_preconditions(self, state) -> bool:
        return all([
            state[0] is None, # has free hand
            not (stack_index := find_block(self.objects[0], state[1])) is None # block exists on table
            and len(state[1][stack_index]) == 1 # single block -  watch the `and` here.
        ])
    
    def _apply_in_place(self, state: tuple[str | int, list[list[str | int]]]) -> None:
        state[0] = self.objects[0] # now holding
        del state[1][find_block(self.objects[0], state[1])] # not on table


class PutdownAction(BlocksAction):
    @staticmethod
    def get_name() -> str:
        return 'putdown'

    @staticmethod
    def get_num_objects() -> int:
        return 1
    
    @classmethod
    def _get_object_selection_functions(cls) -> list[Callable[[tuple[str | int, list[list[str | int]]]], list[str | int]]]:
        return [
            lambda state: [[]]  if state[0] is None else [state[0]] # can only put down the object you are holding
        ]

    def meets_preconditions(self, state) -> bool:
        return state[0] == self.objects[0] # is holding
    
    def _apply_in_place(self, state: tuple[str | int, list[list[str | int]]]) -> None:
        state[1].append([self.objects[0]]) # put on table
        state[0] = None # not holding

class StackAction(BlocksAction):
    @staticmethod
    def get_name() -> str:
        return 'stack'

    @staticmethod
    def get_num_objects() -> int:
        return 2
    
    @classmethod
    def _get_object_selection_functions(cls) -> list[Callable[[tuple[str | int, list[list[str | int]]]], list[str | int]]]:
        return [
            lambda state: [[]]  if state[0] is None else [state[0]], # can only stack the object you are holding
            lambda state: [stack[-1] for stack in state[1]] # can only stack on a top block
        ]

    def meets_preconditions(self, state) -> bool:
        return all([
            state[0] == self.objects[0], # holding the block
            not (stack_index := find_block(self.objects[1], state[1])) is None # destination block exists
            and state[1][stack_index][-1] == self.objects[1] # destination is on top of a stack - watch for the `and` here. 
        ])
    
    def _apply_in_place(self, state: tuple[str | int, list[list[str | int]]]) -> None:
        state[0] = None # not holding
        state[1][find_block(self.objects[1], state[1])].append(self.objects[0]) # stack on top 
    
class UnstackAction(BlocksAction):
    @staticmethod
    def get_name() -> str:
        return 'unstack'

    @staticmethod
    def get_num_objects() -> int:
        return 2
    
    @classmethod
    def _get_object_selection_functions(cls) -> list[Callable[[tuple[str | int, list[list[str | int]]]], list[str | int]]]:
        return [
            lambda state: [stack[-1] for stack in state[1]], # can only unstack from the top
            lambda state: [stack[-2] for stack in state[1] if len(stack) > 1] # can only unstack off the block below
        ]

    def meets_preconditions(self, state) -> bool:
        return all([
            state[0] is None, # hand empty
            not (stack_index := find_block(self.objects[0], state[1])) is None # top block actually exists
            and len(state[1][stack_index]) > 1 # at least 2 blocks in the stack
            and state[1][stack_index][-2] == self.objects[1] # block below matches
        ])
    
    def _apply_in_place(self, state: tuple[str | int, list[list[str | int]]]) -> None:
        state[0] = state[1][find_block(self.objects[0], state[1])].pop() # pops off the block and puts it in holding in one go




