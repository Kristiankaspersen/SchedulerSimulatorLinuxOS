
class RedBlackTree:
    RED = True
    BLACK = False

    class Node:
        def __init__(self, value):
            self.value = value
            self.right = None
            self.left = None
            self.color = RedBlackTree.RED
            self.parent = None
            self.pcb = None

    def __init__(self):
        self.root = None

    def insert(self, value):
        node = self.Node(value)
        if self.root is None:
            self.root = node
            self.root.color = self.BLACK
        else:
            new_node = self.insert_node_iter(node, self.root)
            self.fix_insert(new_node)

    def insert_node_iter(self, inserted_node, current):
        while True:
            if inserted_node.value > current.value:
                if current.right is None:
                    current.right = inserted_node
                    inserted_node.parent = current
                    break
                else:
                    current = current.right
            else:
                if current.left is None:
                    current.left = inserted_node
                    inserted_node.parent = current
                    break
                else:
                    current = current.left
        return inserted_node

    def insert_node_rec(self, inserted_node, next_node):
        if next_node.value > inserted_node.value:
            if next_node.right is None:
                next_node.right = inserted_node
            else:
                self.insert_node_rec(inserted_node, next_node.right)
                # Here we have to do the red-black tree check, if we need to recolor, or reorder. right.
        else:
            if next_node.left is None:
                next_node.left = inserted_node
                # Here we have to do the red-black tree check, if we need to recolor, or reorder. right.
            else:
                self.insert_node_rec(inserted_node, next_node.left)

    def fix_insert(self, node):
        while node != self.root and node.parent.color == self.RED:
            grandparent = node.parent.parent
            if node.parent == grandparent.left:
                uncle = grandparent.right
                if uncle and uncle.color == self.RED:
                    node.parent.color = self.BLACK
                    uncle.color = self.BLACK
                    grandparent.color = self.RED
                    node = grandparent
                else:
                    if node == node.parent.right:
                        node = node.parent
                        self.rotate_left(node)
                    node.parent.color = self.BLACK
                    grandparent.color = self.RED
                    self.rotate_right(grandparent)
            else:
                uncle = grandparent.left
                if uncle and uncle.color == self.RED:
                    node.parent.color = self.BLACK
                    uncle.color = self.BLACK
                    grandparent.color = self.RED
                    node = grandparent
                else:
                    if node == node.parent.left:
                        node = node.parent
                        self.rotate_right(node)
                    node.parent.color = self.BLACK
                    grandparent.color = self.RED
                    self.rotate_left(grandparent)
        self.root.color = self.BLACK

    def rotate_left(self, node):
        new_parent = node.right
        node.right = new_parent.left
        if new_parent.left: # Is not none
            new_parent.left.parent = node
        new_parent.parent = node.parent
        if node.parent is None:
            self.root = new_parent
        elif node == node.parent.left:
            node.parent.left = new_parent
        else:
            node.parent.right = new_parent
        new_parent.left = node
        node.parent = new_parent

    def rotate_right(self, node):
        new_parent = node.left
        node.left = new_parent.right
        if new_parent.right:
            new_parent.right.parent = node
        new_parent.parent = node.parent
        if node.parent is None:
            self.root = new_parent
        elif node == node.parent.right:
            node.parent.right = new_parent
        else:
            node.parent.left = new_parent
        new_parent.right = node
        node.parent = new_parent

    class RedBlackTree:
        RED = True
        BLACK = False

        class Node:
            def __init__(self, value, color):
                self.value = value
                self.color = color  # True = RED, False = BLACK
                self.left = None
                self.right = None
                self.parent = None

        def __init__(self):
            self.root = None

        # .......................... Insertion code .....................
        def insert(self, value):
            new_node = self.Node(value, self.RED)  # New nodes are always RED
            if self.root is None:
                self.root = new_node
                self.root.color = self.BLACK  # Root must always be BLACK
            else:
                self.insert_node(new_node, self.root)
                self.fix_insert(new_node)

        def insert_node(self, inserted_node, next_node):
            if inserted_node.value < next_node.value:
                if next_node.left is None:
                    next_node.left = inserted_node
                    inserted_node.parent = next_node
                else:
                    self.insert_node(inserted_node, next_node.left)
            else:
                if next_node.right is None:
                    next_node.right = inserted_node
                    inserted_node.parent = next_node
                else:
                    self.insert_node(inserted_node, next_node.right)

        # .......................... Deletion code .....................
    def delete(self, value):
        node = self.find_node(self.root, value)
        if node is None:
            return  # Node not found

        self.delete_node(node)

    def delete_node(self, node):
        # If node has two children, find successor and swap values
        if node.left and node.right:
            successor = self.get_min(node.right)
            node.value = successor.value
            node = successor  # Delete successor instead

        # Node now has at most one child
        child = node.left if node.left else node.right

        if child:  # If node has one child, replace it
            self.replace_node(node, child)
            if node.color == self.BLACK:
                self.fix_delete(child)
        else:  # If node has no children
            if node.color == self.BLACK:
                self.fix_delete(node)
            self.replace_node(node, None)

    def fix_delete(self, node):
        while node != self.root and node.color == self.BLACK:
            if node == node.parent.left:
                sibling = node.parent.right
                if sibling and sibling.color == self.RED:  # Case 1: Sibling is RED
                    sibling.color = self.BLACK
                    node.parent.color = self.RED
                    self.rotate_left(node.parent)
                    sibling = node.parent.right

                if (sibling.left is None or sibling.left.color == self.BLACK) and \
                        (
                                sibling.right is None or sibling.right.color == self.BLACK):  # Case 2: Sibling's children are BLACK
                    sibling.color = self.RED
                    node = node.parent
                else:
                    if sibling.right is None or sibling.right.color == self.BLACK:  # Case 3: Sibling's right child is BLACK
                        if sibling.left:
                            sibling.left.color = self.BLACK
                        sibling.color = self.RED
                        self.rotate_right(sibling)
                        sibling = node.parent.right

                    # Case 4: Sibling's right child is RED
                    sibling.color = node.parent.color
                    node.parent.color = self.BLACK
                    if sibling.right:
                        sibling.right.color = self.BLACK
                    self.rotate_left(node.parent)
                    node = self.root

            else:  # Mirror cases if node is right child
                sibling = node.parent.left
                if sibling and sibling.color == self.RED:
                    sibling.color = self.BLACK
                    node.parent.color = self.RED
                    self.rotate_right(node.parent)
                    sibling = node.parent.left

                if (sibling.left is None or sibling.left.color == self.BLACK) and \
                        (sibling.right is None or sibling.right.color == self.BLACK):
                    sibling.color = self.RED
                    node = node.parent
                else:
                    if sibling.left is None or sibling.left.color == self.BLACK:
                        if sibling.right:
                            sibling.right.color = self.BLACK
                        sibling.color = self.RED
                        self.rotate_left(sibling)
                        sibling = node.parent.left

                    sibling.color = node.parent.color
                    node.parent.color = self.BLACK
                    if sibling.left:
                        sibling.left.color = self.BLACK
                    self.rotate_right(node.parent)
                    node = self.root

        node.color = self.BLACK  # Ensure node is black

    def find_node(self, root, value):
        if root is None or root.value == value:
            return root
        if value < root.value:
            return self.find_node(root.left, value)
        return self.find_node(root.right, value)

    def get_min(self, node):
        while node.left:
            node = node.left
        return node

    def replace_node(self, node, new_node):
        if node.parent is None:
            self.root = new_node
        elif node == node.parent.left:
            node.parent.left = new_node
        else:
            node.parent.right = new_node
        if new_node:
            new_node.parent = node.parent






