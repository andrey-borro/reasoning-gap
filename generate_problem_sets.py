import math
import random
import os
import json

# BLOCKSWORLD - algorithm taken from the paper 
# Slaney, John, and Sylvie Thiébaux. 2001. “Blocks World Revisited.” Artificial Intelligence 125 (1–2): 119–53.

# def print_r_table(r_table: list[list[float]]):
#     print('  ', ' '.join(f' {i} ' for i in range(len(r_table[0]))))
#     for index, row in enumerate(r_table):
#         print(f'{index} ', ' '.join('---' if x is None else f'{x:.1f}' for x in row))

# def g_function(n: int, k: int) -> int:
#     """
#         n: Number of ungrounded towers.
#         k: Number of grounded ones.
#     """ 
#     def internal_func(n, k, i):
#         return math.comb(n, i) * math.prod(range(k + i, n + k))
    
#     return sum(internal_func(n, k, i) for i in range(0, n + 1))

def generate_r_table(size: int) -> list[list[float]]:
    """ Generates the table of R-relations between the number of
        grounded towers and the number of ungrounded towers used
        for probability calculations.

        Returns: R-Table[ungrounded (phi)][grounded (tau)].

        phi 0 and tau size, and all phi + tau > size are not possible.
    """
    r_table = [[None for _ in range(size + 1)] for _ in range(size + 1)]
    r_table[1] = [1 for _ in range(size + 1)]
    for phi in range(2, size + 1):
        for tau in range(size - phi + 1):
            top_line = r_table[phi - 1][tau] * (phi - 1 + tau + r_table[phi - 1][tau + 1])
            bottom_line = phi - 2 + tau + r_table[phi - 1][tau]
            r_table[phi][tau] = top_line / bottom_line
    return r_table


def _generate_blocksworld_state(num_blocks: int, r_table: list[list[float]]) -> list[list[int]]:
    """Generates a random blocksworld table with `num_blocks` blocks.
    
    The output is `list[list[int]]` where the outer (unordered) list holds stacks of blocks.
    The inner lists are the stacks and are ordered `bottom -> top`
    """
    grounded = []
    ungrounded = [[i] for i in range(num_blocks)]

    while len(ungrounded) > 0: #until all towers are grounded
        phi = len(ungrounded)
        tau = len(grounded)
        index = random.randrange(phi) # select an ungrounded tower at random 

        table_probability = (r_table[phi][tau]) / (r_table[phi][tau] + phi + tau - 1)
        if random.random() < table_probability: # select table according to probability ratio
            grounded.append(ungrounded[index]) # place the tower into the table
        else:
            all_towers = grounded + [tower for tower in ungrounded if not tower == ungrounded[index]]
            selected = random.choice(all_towers) # select from all towers with uniform probability
            selected.extend(ungrounded[index]) # put the ungrounded tower on top of the selected one

        ungrounded.pop(index)
    
    return grounded

def _generate_blocksworld_states(num_states: int, num_blocks_range: tuple[int, int]):
    """Generates `num_states` BlocksWorld states at random. 
    The number of blocks is determined by `block_range`, which functions like `range()` and is selected uniformly."""
    if not num_blocks_range[1] > num_blocks_range[0]:
        raise ValueError(f'Weird range: ({num_blocks_range[0]}, {num_blocks_range[1]})')
    
    r_table = generate_r_table(num_blocks_range[1])

    states = []

    for _ in range(num_states):
        num_blocks = random.randrange(num_blocks_range[0], num_blocks_range[1])
        state = _generate_blocksworld_state(num_blocks, r_table)
        states.append(state)
    
    return states

def get_moves_for_stack(stack: list[int], global_max: int) -> int:
    """Internal function to predict the number of moves that it will take to fully move a stack into its goal postitions."""
    # search through the stack to find the max. everything above the max will need to be moved twice. 
    # the max will only ever need to be moved once (this is trivial). below the max, this process is repeated.

    if len(stack) == 0:
        return 0

    if stack[0] == global_max: #this stack is a little bit special
        next_index = 1
        next_block = global_max - 1
        while next_index < len(stack) and stack[next_index] == next_block:
            next_index += 1
            next_block -= 1
        
        moves = 2 * (len(stack) - next_index)
        # print(f'Stack {stack} is part of the main tower. Clearing the top blocks takes {moves} moves.')
        return moves # basically, we have to move all of the out-of-order blocks off the main tower
        
    # this is the code for a regular stack 

    if len(stack) == 1: # stacks of one block only ever need to be placed on the main tower.
        # print(f'Block {stack} only takes one move.')
        return 1

    max_index = 0
    max_value = stack[max_index]

    for index, value in enumerate(stack):
        if value > max_value:
            max_value = value
            max_index = index
    
    # 2 moves for everything above + 1 move for the max + variable number for the ones below
    moves = 2 * (len(stack) - max_index - 1) + 1 + get_moves_for_stack(stack[:max_index], global_max)
    # print(f'Moving {stack} takes {moves} moves, max_index was {max_index}')
    return moves


def get_solution_length(state: list[list[int]]) -> int:
    """Returns the number of steps required to solve a BlocksWorld task starting at `state` and finishing at `max_block, ..., 0`"""
    # asssumes the end goal is to stack the blocks with 0 at the top.
    # state is [[stack1] [stack2] ... ] where [stack is bottom -> top]
    global_max = len(sum(state, [])) - 1
    return sum(2 * get_moves_for_stack(stack, global_max) for stack in state)

def generate_unique_problem_set(num_problems: int, block_range: tuple[int, int], cost_range: tuple[int, int]) -> list[tuple[int, list[list[int]]]]:
    """
        Generates `num_problems` states with `block_range` blocks and solutions bounded by `cost_range`. 
        All ranges work as normal, but `cost_range` should be used in multiples of two.

        Returns list of tuples `[cost, state]`.
    """
    state_list = []
    while len(state_list) < num_problems:
        for generated_state in _generate_blocksworld_states(num_problems, block_range):
            solution_length = get_solution_length(generated_state)
            if cost_range[0] <= solution_length < cost_range[1]: # filter out the ones outside of our net
                generated_state = sorted(generated_state) # to deal with shuffled stacks
                if not generated_state in state_list:
                    state_list.append((solution_length, generated_state))

    return state_list[:num_problems] # this does not into account biases in selection caused by the cost_range filtering, i.e. costs are not at all uniform within the final output.

def create_blocksworld_problem_json(problem_set: list[tuple[int, list[list[int]]]], problem_set_file_path: str):
    """Problem set is list[(cost, state)...]. Creates `set_file_name` json file."""
    if os.path.exists(problem_set_file_path) and not input(f'File {problem_set_file_path} already exists. Overwrite? (Y/N): ').strip().upper() == 'Y':
        print('Problem set creation aborted.')
        return
    
    data = [
        {
            'tag': f'prob_{index:04}',
            'optimal_cost' : cost,
            'state' : state,
            'num_blocks' : len(sum(state, []))
        }
        for index, (cost, state) in enumerate(problem_set)
    ]

    with open(problem_set_file_path, 'w') as write_file:
        json.dump(data, write_file)


# CRT - The templates are taken from the supplementary material of 
# Hagendorff, Thilo, Sarah Fabi, and Michal Kosinski. 2023. 
# “Human-like Intuitive Behavior and Reasoning Biases Emerged in Large Language Models but Disappeared in ChatGPT.” 
# Nature Computational Science 3 (10): 833–38.
# https://static-content.springer.com/esm/art%3A10.1038%2Fs43588-023-00527-x/MediaObjects/43588_2023_527_MOESM1_ESM.pdf

def generate_crt_problem(template: str) -> tuple[str, dict]:
    """ Takes a CRT template as `str` and returns a `tuple[str, dict]` with an instantiated question and an answer of form:

        { 'A' : `int`, 'Y' : `int` }
    
        The ranges used for the instantiation variables are hardcoded into the function. 
    """
    # increase by a factor of (2-5) every (2-6)X days from (6-10)Y to 1/(X-val)^(1-3)
    grow_rate = random.randrange(2,6)
    rate_period = random.randrange(2,7)
    completion_time = random.randrange(6,11)
    steps_back = random.randrange(1, 4)

    target: str = f'1/{grow_rate**steps_back}'

    # code for full_num, part_num - this is done because the templates have two
    # different ways of setting up the question. Some use fractions and some use
    # a specific full and partial value.
    part_num = random.randrange(5, 15)
    full_num = part_num * (grow_rate**steps_back)

    answer = {'A' : completion_time, 'B': steps_back * rate_period}

    rate_lingo = {
        2 : 'double',
        3: 'triple',
        4: 'quadruple',
        5: 'quintuple'
    }

    try:
        problem_text = template.format(grow_rate = rate_lingo[grow_rate], rate_period = f'{rate_period}X', completion_time = f'{completion_time}Y', target = target)
    except KeyError:
        problem_text = template.format(grow_rate = rate_lingo[grow_rate], rate_period = f'{rate_period}X', completion_time = f'{completion_time}Y', part_num = str(part_num), full_num = str(full_num))
    return (problem_text + ' X and Y are both numbers, you can use them to represent the final answer. Please think step by step.', answer)

def generate_crt_problems(num_repeats: int, templates_file_path: str, output_file_path: str) -> None:
    """ Instantiates `num_repeats` problems for every template in the json file at `templates_file_path`. 
        Stores the questions and answers as a dictionary in json form at `output_file_path`. 
    """
    with open(templates_file_path) as infile:
        prob_dict = json.load(infile)

    problems = []
    for template in prob_dict.values():
        for _ in range(num_repeats):
            problems.append(generate_crt_problem(template))

    random.shuffle(problems)
    
    out_dict = {
        f'crt_prob_{i:04}' : {
            'question': line[0],
            'answer': line[1]
        }
        for i, line in enumerate(problems)
    }

    with open(output_file_path, 'w') as outfile:
        json.dump(out_dict, outfile, indent = 2)








