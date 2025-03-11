from typing import Literal

from block_code import state_to_pddl, goal_from_state

BLOCKSWORLD_STRATEGY_HEADER = \
"""----
A strategy guide for solving this PDDL domain is given below. Stick to the solution overview closely and use it in your reasoning process. 
Pay particular attention to the common errors outlined.

{strategy_text}
----"""

BLOCKSWORLD_DOMAIN = \
"""
action : pickup (block)
preconds : (clear block), (ontable block), (handempty)
effects : (holding block), not(ontable block), not(clear block), not(handempty)

action : putdown (block)
preconds : (holding block)
effects : not(holding block), (clear block), (ontable block), (handempty)

action : unstack (top-block bottom-block)
preconds : (on top-block bottom-block), (clear top-block), (handempty)
effects : (holding top-block), (clear bottom-block), not(on top-block bottom-block), not(clear bottom-block), not(handempty)

action : stack (top-block bottom-block)
preconds : (holding top-block), (clear bottom-block)
effects : (on top-block bottom-block), (clear top-block), (handempty), not(holding top-block), not(clear bottom-block)
"""

BLOCKSWORLD_TASK_PROMPT = \
'Consider the following PDDL domain with 4 operators:' + BLOCKSWORLD_DOMAIN + \
"""
{optional_strategy}

An example solution (without reasoning steps) would look like:
(unstack d c)
(putdown d)
(pickup c)
(stack c d)
(unstack a b)
(putdown a)
(pickup b)
(stack b c)
(pickup a)
(stack a b)

*THIS IS YOUR PROBLEM, SOLVE IT*:
Initial State:
{initial_state}

Goal:
{goal_state}
Solution:"""

BLOCKSWORLD_SUMMARY_PROMPT = \
"""Summarise the given solution into one action per line, with the first action on the first line of input,  with no other numbering, text or formatting, except for the brackets around the actions. 

e.g.

(move rooma roomb)
(pickup balla roomb)
"""

PDDL_FIX_PROMPT_NOTEXEC = \
"""Your solution is executable until action {last_exec_action} (which is not executable). 

After executing the solution until this action, the current state is:
{final_state}

Identify the error and give back a new, correct solution.
""" # TODO - last_exec_action is probably the wrong name then. 

PDDL_FIX_PROMPT_NOTGOAL = \
"""The answer is executable, but the final state is incorrect.  

The final state after executing your solution state is:
{final_state}

Identify the error and give back a new, correct solution.
"""

BLOCKSWORLD_STRATEGY_PROMPT = \
"""You will be given a PDDL domain, as well as an example problem and solution for that domain. Your goal is to write a strategy for the domain which will be used as part of a prompt for a weaker LLM to solve this problem. The strategy should be threefold. 

---
Firstly, a brief overview of the high-level dynamics, e.g. how the actions interact and what they are used for in the domain. Do not just repeat the preconditions and effects in PDDL - the LLM will have access to these. Instead, use English to explain the environment and how the actions are used to do things in it. Finish this overview with a brief list of key constraints about objects within this environment (see example).

Secondly, a high-level guide to solving a general problem within this domain. The guide should open with "To solve the problem, follow these step-by-step instructions:". Follow this with an instruction step outlining how to interpret the goal configuration in the context of planning your solution. After this, give simple and clear instructions on how to solve the task, step-by-step. Remember that you are talking to an LLM. It has no memory or space to "visualise" a problem, nor does it respond well to being philosophical. Instead, give clear and very simple actionable instructions for it to follow. Each instruction should represent a "big picture" step for the agent to follow. Then, explain how to achieve that step in sub-instructions. Absolutely prioritise the most simple (to understand and follow) instructions, even if it means having a longer solution. Do not forget that the LLM executing this is weak, and should not try to do complex reasoning if it can be avoided. Your job is to do as much of the thinking as you can, and to give it clear steps to take action on.

Thirdly, give a list (at most five) of common mistakes that you assume a weaker LLM is likely to make and how to avoid them. Prioritise the ones that you think might be most likely to stump the LLM. 

Throughout the strategy, feel free to use general examples (but keep them very short and concise, as they should not take up much of the strategy at all).

---

A (slightly less detailed than you should aim for) example for the gripper domain could look like:

Domain Overview:
The domain consists of balls (e.g. balla, ballb, ballc) in rooms (rooma, roomb ....), with a robot that travels between the two rooms. The robot can only pick up to two balls at a time using the pickup action - one in each hand, specified as part of the action e.g. (pickup balla rooma left), and only when they are with him in the room that he is currently on. The robot moves between rooms using the move action, taking the balls in his hands with him, and dropping a ball will drop it into the room that the robot is currently in. 

Key Constraints
 - the robot can hold at most 2 balls
 - balls must be in the same room as the robot to be picked up
 - the robot must have a free hand to pick up a ball

Solution Overview:
To solve the problem, follow these step-by-step instructions:
1. Observe the required goal location for the balls e.g. (at roomb balla)
2. Move the robot to the location of a ball that needs to move
- ensure that it has dropped off whichever balls it was moving prior
3. pick up the ball, as well as any other ball (if any) that is in the same room and needs to go to the same destination room
- (short example)
4. move the robot to the destination room and drop whichever balls it is holding and need to be in that room
5. repeat this process until all balls are where they need to be, tracking which balls remain

Common Mistakes:
Do not pick up balls once they are in the room where they need to be, they do not need to be touched again. 
Do not try and pick up balls if they are in different rooms, the robot can only pick up balls in the same room. 
etc. 

---

The PDDL domain that you are writing the strategy for:""" + BLOCKSWORLD_DOMAIN + \
"""Here is an example problem within this domain:

Initial State:
(clear a)
(clear d)
(handempty)
(on a b)
(on d c)
(ontable b)
(ontable c)

Goal:
(on a b)
(on b c)
(on c d)

Solution:
(unstack d c)
(putdown d)
(pickup c)
(stack c d)
(unstack a b)
(putdown a)
(pickup b)
(stack b c)
(pickup a)
(stack a b)
"""

CRT_MAIN_PROMPT = \
"""Solve the following problem. Give a formula enclosed in double at symbols as your final answer at the end, e.g. @@ANSWER_HERE@@

{crt_problem}
{strategy_text}
"""

CRT_STRATEGY_TEXT = """
A general strategy for this problem type has been given below.

{strategy}
"""

CRT_SUMMARY_PROMPT = \
"""
Summarise the given formula into an AY - BX form, and put that into a json format, as shown below. Give only the json as your output, with no other text or formatting.  If it is not possible, then assign None to A and B.

{
  'A' : some_int,
  'B' : some_int
}

Make sure that you don't make a mistake with negatives. If the answer is 10Y - 5X, then A is 10 and B is 5 (not negative 5).
"""

CRT_STRATEGY_PROMPT = """
Take the below problem:

After a switch is flicked, the area of light shining within a room triples every 5X nanoseconds until it fills the room. If it takes 7Y nanoseconds for the room to fill,  how many nanoseconds after the switch was flicked was the room at 1/9 full?

I want you to write an explanation for a weaker LLM on how to solve similar problems. Note that the problems will have different numbers, thematic settings or even twists on algebraic variables, so make your strategy generalised.
"""

def get_blocksworld_task_prompt(state: tuple[str | int, list[list[str | int]]], strategy: str | None = None) -> str:
    """Returns the prompt for solving a BlocksWorld PDDL task.
    
        - `state` is a BlocksWorld state [holding block, blocks_on_table]. 
        - `strategy` is the generalised strategy (`None` if no strategy).
    """
    goal = goal_from_state(state)
    initial_state_text = '\n'.join(state_to_pddl(state))
    goal_state_text = '\n'.join(state_to_pddl(goal, is_goal = True))
    return BLOCKSWORLD_TASK_PROMPT.format(
        initial_state = initial_state_text, 
        goal_state = goal_state_text,
        optional_strategy = BLOCKSWORLD_STRATEGY_HEADER.format(strategy_text = strategy) if strategy else ''
    )


def get_blocksworld_fix_prompt(prompt_type: Literal['NOTGOAL', 'NOTEXECUTABLE'], last_action: list[str], final_state: tuple[str | int, list[list[str | int]]]):
    """Returns the prompt for fixing a BlocksWorld PDDL solution. 
    
        - `prompt_type` determines prompt phrasing
        - `last_action` is the last exec action; (pddl_action) string.
        - `final_state` the state that the evaluation finished on. 
    """

    if not prompt_type in ('NOTGOAL', 'NOTEXECUTABLE'):
        raise ValueError(f'Weird fix_prompt type: {prompt_type}')
    
    final_state_pddl = '\n'.join(state_to_pddl(final_state))

    if prompt_type == 'NOTGOAL':
        return PDDL_FIX_PROMPT_NOTGOAL.format(final_state = final_state_pddl)

    if prompt_type == 'NOTEXECUTABLE':
        return PDDL_FIX_PROMPT_NOTEXEC.format(last_exec_action = last_action, final_state = final_state_pddl)
    

def get_crt_task_prompt(crt_problem: str, strategy: str | None):
    """Returns the prompt for solving a CRT task. `crt_problem` is the text description of the problem. `strategy` is the generalised strategy (`None` if none)."""
    if strategy is None:
        return CRT_MAIN_PROMPT.format(crt_problem = crt_problem, strategy_text = '')
    else:
        return CRT_MAIN_PROMPT.format(crt_problem = crt_problem, strategy_text = CRT_STRATEGY_TEXT.format(strategy = strategy))