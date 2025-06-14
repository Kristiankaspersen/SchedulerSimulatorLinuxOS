
# tests/test_tree.py
# Here I want to check if all properties are obtained in the tree.

import pytest

from schedsimulator.enums.task_type import TaskType
from schedsimulator.structures.red_black_tree import RedBlackTree
from schedsimulator.processes.process import Process
from schedsimulator.structures.task import Task

BLACK = False
RED = True


##### First check if all properties are valid in the tree #####


# 0. Check if values are in correct BST order (just check that its in fact a BST tree)
def test1_insert_structure_and_root_color():
    tree = RedBlackTree()
    values = [10, 20, 30, 15, 25, 15, 40]
    i = 0
    for val in values:
        task = Task(TaskType.CPU,i)
        task.deadline = val
        tree.insert(task)
        i += 1

    # Check values are in correct BST order
    in_order = []

    def inorder(node):
        if node is None:
            return
        if node:
            inorder(node.left)
            in_order.append(node.value)
            inorder(node.right)

    inorder(tree.root)
    assert in_order == sorted(values)


#1. Root is always black (check starting props)
def test2_root_node_props_insert():
    tree = RedBlackTree()
    task = Task(TaskType.CPU,0)
    task.deadline = 1
    tree.insert(task)
    assert tree.root
    assert tree.root.task.deadline == 1
    assert tree.root.left is None
    assert tree.root.right is None
    assert tree.root.parent is None
    assert tree.root.color is BLACK

#1.1 Root is always black (check that it never changes color)
def test3_root_color():
    tree = RedBlackTree()
    values = [10, 20, 30, 15, 25, 15, 40]
    i = 0
    for val in values:
        task = Task(TaskType.CPU, i)
        task.deadline = val
        tree.insert(task)
        i += 1

    assert tree.root is not None
    assert tree.root.color == BLACK
    #TODO Do more insertions and deletions and check again

#3. Each node is either RED or BLACK
def test4_nodes_either_red_or_black():
    tree = RedBlackTree()
    values = [10, 20, 30, 15, 25, 15, 40, 20, 30, 40, 21, 32, 21, 32]
    i = 0
    for val in values:
        task = Task(TaskType.CPU, i)
        task.deadline = val
        tree.insert(task)
        i += 1

    def check_color(node):
        if node is None:
            return True
        assert node.color in (RED, BLACK), f"Node {node.value} has invalid color: {node.color}"
        return check_color(node.left) and check_color(node.right)

    assert check_color(tree.root)

#3. No RED node with red children or parents:
def test5_no_red_red_violation_insert():
    tree = RedBlackTree()
    i = 0
    for value in [10, 20, 30, 15, 25, 15, 25, 80, 30]:
        task = Task(TaskType.CPU, i)
        task.virtual_deadline = value
        tree.insert(task)
        i += 1

    def check(node):
        if node is None:
            return True
        if node.color == RED:
            if (node.left and node.left.color == RED) or \
               (node.right and node.right.color == RED):
                return False
        return check(node.left) and check(node.right)

    assert check(tree.root)
def test6_no_red_red_violation_deletion():
    # TODO do somethign here
    pass

# 4. There has to be the same number of black nodes on each path to the None pointers
def test7_same_amount_of_black_in_all_paths():
    tree = RedBlackTree()
    values = [10, 20, 30, 15, 25, 40, 5, 3, 7, 2, 1]
    i = 0
    for val in values:
        task = Task(TaskType.CPU, i)
        task.deadline = val
        tree.insert(task)
        i += 1

    def check_black_height(node):
        if node is None:
            return 1  # Null leaf counts as 1 black node

        left = check_black_height(node.left)
        right = check_black_height(node.right)

        # Return 0 immediately if imbalance detected downstream
        if left == 0 or right == 0 or left != right:
            return 0

        return left + (1 if node.color == BLACK else 0)

    assert check_black_height(tree.root) != 0, "Black-height is not consistent across paths"


# 5. Check that the tree is balanced (height is bounded)
def test8_tree_is_balanced():
    tree = RedBlackTree()
    values = [10, 20, 30, 15, 25, 5, 1, 2, 3, 40, 50, 60, 35]
    i = 0
    for val in values:
        task = Task(TaskType.CPU,i)
        task.deadline = val
        tree.insert(task)
        i += 1

    def min_height(node):
        if node is None:
            return 0
        return 1 + min(min_height(node.left), min_height(node.right))

    def max_height(node):
        if node is None:
            return 0
        return 1 + max(max_height(node.left), max_height(node.right))

    min_h = min_height(tree.root)
    max_h = max_height(tree.root)

    assert max_h <= 2 * min_h, (
        f"Tree is too unbalanced: max height {max_h}, min height {min_h}"
    )


def test9_bst_order_after_deletion():
    tree = RedBlackTree()
    values = [20, 10, 30, 15, 25, 10]
    for i, val in enumerate(values):
        task = Task(TaskType.CPU, i)
        task.deadline = val
        tree.insert(task)

    # Delete one 10
    tree.delete(10)
    values.remove(10)  # only remove one

    in_order = []
    def inorder(node):
        if node:
            inorder(node.left)
            in_order.append(node.task.deadline)
            inorder(node.right)
    inorder(tree.root)

    assert in_order == sorted(values)

    # Delete 30
    tree.delete(30)
    values.remove(30)

    in_order = []
    inorder(tree.root)

    assert in_order == sorted(values)

# Deletion tests
# def test9_bst_order_after_deletion():
#     tree = RedBlackTree()
#     values = [20, 10, 30, 15, 25, 10]
#     i = 0
#     for val in values:
#         task = Task(TaskType.CPU, i)
#         task.deadline = val
#         tree.insert(task)
#         i += 1
#     tree.delete(10)




def test10_root_black_after_deletion():
    tree = RedBlackTree()
    values = [50, 30, 70, 20, 40, 60, 80]
    i = 0
    for val in values:
        task = Task(TaskType.CPU, i)
        task.deadline = val
        tree.insert(task)
        i += 1

    # This delete based on value so its correct I guess.
    tree.delete(50)
    assert tree.root.color == BLACK
    tree.delete(60)
    assert tree.root.color == BLACK
    tree.delete(40)
    assert tree.root.color == BLACK
    tree.delete(30)
    assert tree.root.color == BLACK
    tree.delete(70)
    assert tree.root.color == BLACK
    tree.delete(80)
    assert tree.root.color == BLACK
    tree.delete(20)
    assert tree.root is None

def test11_node_colors_after_deletion():
    tree = RedBlackTree()
    values = [10, 20, 30, 15, 25, 5, 1]
    i = 0
    for val in values:
        task = Task(TaskType.CPU, i)
        task.virtual_deadline = val
        tree.insert(task)
        i += 1
    tree.delete(20)

    def check_colors(node):
        if node is None:
            return True
        assert node.color in (RED, BLACK), f"Invalid color on node {node.value}"
        return check_colors(node.left) and check_colors(node.right)

    assert check_colors(tree.root)

def test12_no_red_red_after_deletion():
    tree = RedBlackTree()
    values =  [10, 20, 30, 15, 25, 5, 1]
    i = 0
    for val in values:
        process = Task(TaskType.CPU, i)
        process.deadline = val
        tree.insert(process)
        i += 1

    tree.delete(15)

    def check_no_red_red(node):
        if node is None:
            return True
        if node.color == RED:
            if (node.left and node.left.color == RED) or \
               (node.right and node.right.color == RED):
                return False
        return check_no_red_red(node.left) and check_no_red_red(node.right)

    assert check_no_red_red(tree.root)

def test13_black_height_after_deletion():
    tree = RedBlackTree()
    values = [10, 20, 30, 15, 25, 5, 1]
    i = 0
    for val in values:
        task = Task(TaskType.CPU, i)
        task.deadline = val
        tree.insert(task)
        i += 1
    tree.delete(25)

    def check_black_height(node):
        if node is None:
            return 1
        left = check_black_height(node.left)
        right = check_black_height(node.right)
        if left == 0 or right == 0 or left != right:
            return 0
        return left + (1 if node.color == BLACK else 0)

    assert check_black_height(tree.root) != 0

def test14_tree_balance_after_deletion():
    tree = RedBlackTree()
    values = [10, 20, 30, 15, 25, 5, 1, 40, 50]
    i = 0
    for val in values:
        task = Task(TaskType.CPU, i)
        task.deadline = val
        tree.insert(task)
        i += 1
    tree.delete(30)

    def min_height(node):
        if node is None:
            return 0
        return 1 + min(min_height(node.left), min_height(node.right))

    def max_height(node):
        if node is None:
            return 0
        return 1 + max(max_height(node.left), max_height(node.right))

    min_h = min_height(tree.root)
    max_h = max_height(tree.root)
    assert max_h <= 2 * min_h


# Min_vruntime
def test_min_vruntime_after_inserts():
    tree = RedBlackTree()
    vruntimes = [50, 30, 70, 20, 60]
    tasks = []

    for i, v in enumerate(vruntimes):
        task = Task(TaskType.CPU, i)
        task.vruntime = v
        task.deadline = v + 2  # assuming you're sorting by deadline
        tasks.append(task)
        tree.insert(task)

        # Debug print of all task nodes
        print("\n=== Task Node States ===")
        for t in tasks:
            if t.rb_node:
                print(f"pid={t.pid}, vruntime={t.vruntime}, node.min_vruntime={t.rb_node.min_vruntime}")
            else:
                print(f"pid={t.pid}, vruntime={t.vruntime}, node is missing")

        #  Debug print of root and children
        print("\n=== Tree Root State ===")
        print(f"ROOT: {tree.root.task.vruntime}, min_vruntime: {tree.root.min_vruntime}")
        if tree.root.left:
            print(f"LEFT: {tree.root.left.task.vruntime}, min_vruntime: {tree.root.left.min_vruntime}")
        if tree.root.right:
            print(f"RIGHT: {tree.root.right.task.vruntime}, min_vruntime: {tree.root.right.min_vruntime}")

    # After all inserts, root.min_vruntime should be the smallest vruntime inserted
    assert tree.root.min_vruntime == min(vruntimes), f"Expected {min(vruntimes)}, got {tree.root.min_vruntime}"

def test_min_vruntime_after_deletions():
    tree = RedBlackTree()
    vruntimes = [50, 30, 70, 20, 60]
    tasks = []

    # Insert all tasks
    for i, v in enumerate(vruntimes):
        task = Task(TaskType.CPU, i)
        task.vruntime = v
        task.deadline = v + 2  # sorting key
        tasks.append(task)
        tree.insert(task)

    #  Reconfirm min before deletion
    expected_min = min(vruntimes)
    assert tree.root.min_vruntime == expected_min, f"Expected {expected_min}, got {tree.root.min_vruntime}"

    # Delete the task with the minimum vruntime
    min_task = next(t for t in tasks if t.vruntime == expected_min)
    tree.remove(min_task)

    # Remove from local list too
    tasks.remove(min_task)
    remaining_vruntimes = [t.vruntime for t in tasks]

    # After deletion, min_vruntime should match the next smallest
    new_expected_min = min(remaining_vruntimes)
    assert tree.root.min_vruntime == new_expected_min, f"Expected {new_expected_min}, got {tree.root.min_vruntime}"

    # Final print for confirmation
    print("\nAfter Deletion:")
    print(f"Deleted pid={min_task.pid}, vruntime={min_task.vruntime}")
    print(f"New expected min: {new_expected_min}")
    print(f"Tree root min_vruntime: {tree.root.min_vruntime}")
