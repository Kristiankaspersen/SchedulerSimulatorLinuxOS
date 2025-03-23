
# tests/test_tree.py
# Here I want to check if all properties are obtained in the tree.

import pytest
from schedsimulator.structures.red_black_tree import RedBlackTree

BLACK = False
RED = True


##### First check if all properties are valid in the tree #####


# 0. Check if values are in correct BST order (just check that its in fact a BST tree)
def test_insert_structure_and_root_color():
    tree = RedBlackTree()
    values = [10, 20, 30, 15, 25, 15, 40]
    for val in values:
        tree.insert(val)

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
def test_root_node_props_insert():
    tree = RedBlackTree()
    tree.insert(1)
    assert tree.root
    assert tree.root.value == 1
    assert tree.root.left is None
    assert tree.root.right is None
    # This should fail later, when i also insert the PCB.
    assert tree.root.pcb is None
    assert tree.root.parent is None
    assert tree.root.color is BLACK

#1.1 Root is always black (check that it never changes color)
def test_root_color():
    tree = RedBlackTree()
    values = [10, 20, 30, 15, 25, 15, 40]
    for val in values:
        tree.insert(val)

    assert tree.root is not None
    assert tree.root.color == BLACK
    # Do more insertions and deletions and check again

#3. Each node is either RED or BLACK
def test_nodes_either_red_or_black():
    tree = RedBlackTree()
    values = [10, 20, 30, 15, 25, 15, 40, 20, 30, 40, 21, 32, 21, 32]
    for val in values:
        tree.insert(val)

    def check_color(node):
        if node is None:
            return True
        assert node.color in (RED, BLACK), f"Node {node.value} has invalid color: {node.color}"
        return check_color(node.left) and check_color(node.right)

    assert check_color(tree.root)

#3. No RED node with red children or parents:
def test_no_red_red_violation_insert():
    tree = RedBlackTree()
    for value in [10, 20, 30, 15, 25, 15, 25, 80, 30]:
        tree.insert(value)

    def check(node):
        if node is None:
            return True
        if node.color == RED:
            if (node.left and node.left.color == RED) or \
               (node.right and node.right.color == RED):
                return False
        return check(node.left) and check(node.right)

    assert check(tree.root)
def test_no_red_red_violation_deletion():
    pass

# 4. There has to be the same number of black nodes on each path to the None pointers
def test_same_amount_of_black_in_all_paths():
    tree = RedBlackTree()
    values = [10, 20, 30, 15, 25, 40, 5, 3, 7, 2, 1]
    for val in values:
        tree.insert(val)

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
def test_tree_is_balanced():
    tree = RedBlackTree()
    values = [10, 20, 30, 15, 25, 5, 1, 2, 3, 40, 50, 60, 35]
    for val in values:
        tree.insert(val)

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

# Deletion tests
def test_bst_order_after_deletion():
    tree = RedBlackTree()
    values = [20, 10, 30, 15, 25, 10]
    for v in values:
        tree.insert(v)
    tree.delete(10)

    in_order = []
    def inorder(node):
        if node:
            inorder(node.left)
            in_order.append(node.value)
            inorder(node.right)

    inorder(tree.root)
    #assert in_order == sorted(set(values) - {10})
    values.pop(1)
    assert in_order == sorted(values)
    tree.delete(30)

    in_order = []

    def inorder(node):
        if node:
            inorder(node.left)
            in_order.append(node.value)
            inorder(node.right)

    inorder(tree.root)
    values.pop(1)
    #assert in_order == sorted(set(values) - {10} - {30})
    assert in_order == sorted(values)



def test_root_black_after_deletion():
    tree = RedBlackTree()
    for v in [50, 30, 70, 20, 40, 60, 80]:
        tree.insert(v)
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

def test_node_colors_after_deletion():
    tree = RedBlackTree()
    for v in [10, 20, 30, 15, 25, 5, 1]:
        tree.insert(v)
    tree.delete(20)

    def check_colors(node):
        if node is None:
            return True
        assert node.color in (RED, BLACK), f"Invalid color on node {node.value}"
        return check_colors(node.left) and check_colors(node.right)

    assert check_colors(tree.root)

def test_no_red_red_after_deletion():
    tree = RedBlackTree()
    for v in [10, 20, 30, 15, 25, 5, 1]:
        tree.insert(v)
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

def test_black_height_after_deletion():
    tree = RedBlackTree()
    for v in [10, 20, 30, 15, 25, 5, 1]:
        tree.insert(v)
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

def test_tree_balance_after_deletion():
    tree = RedBlackTree()
    for v in [10, 20, 30, 15, 25, 5, 1, 40, 50]:
        tree.insert(v)
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
