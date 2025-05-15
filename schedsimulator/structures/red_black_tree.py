
class RedBlackTree:
    RED = True
    BLACK = False

    class Node:
        def __init__(self, task):
            self.value = task.deadline  # sorted byt this now.
            self.right = None
            self.left = None
            self.color = RedBlackTree.RED
            self.parent = None
            self.task = task
            self.min_vruntime = task.vruntime

    def __init__(self):
        self.root = None

    def recompute_min_vruntime(self, node):
        if node is None:
            return
        left_min = node.left.min_vruntime if node.left else float('inf')
        right_min = node.right.min_vruntime if node.right else float('inf')
        node.min_vruntime = min(node.task.vruntime, left_min, right_min)

    def update_min_vruntime_up(self, node):
        while node:
            left_min = node.left.min_vruntime if node.left else float('inf')
            right_min = node.right.min_vruntime if node.right else float('inf')
            new_min = min(node.task.vruntime, left_min, right_min)

            if node.min_vruntime == new_min:
                # Nothing changed, we can stop early
                break

            node.min_vruntime = new_min
            node = node.parent  # Move up the tree

    def insert(self, task):
        assert task.rb_node is None, f"BUG: Task pid={task.pid} already in tree"
        node = self.Node(task)
        task.rb_node = node
        if self.root is None:
            self.root = node
            self.root.color = self.BLACK
        else:
            new_node = self.insert_node_iter(node, self.root)
            # And here just store min_vruntime up the tree, and I guess I am fine.

            self.insert_min_vruntime(new_node)
            #self.update_min_vruntime_up(new_node)
            self.fix_insert(new_node)
            #self.update_min_vruntime_up(new_node)
            #self.update_min_vruntime_up(new_node)
            # Think this is wrong, this happens in update_min_vruntime at every tiick, and we just need to make sure that root is updated.
        #self.update_min_vruntime_up(self.root)

    def recompute_all_min_vruntime(self, node):
        if node is None:
            return float('inf')
        left_min = self.recompute_all_min_vruntime(node.left)
        right_min = self.recompute_all_min_vruntime(node.right)
        node.min_vruntime = min(node.task.vruntime, left_min, right_min)
        return node.min_vruntime

    def print_all_nodes(self, node):
        if node is None:
            return
        self.print_all_nodes(node.left)
        print(f"pid={node.task.pid}, vruntime={node.task.vruntime}, min_vruntime={node.min_vruntime}")
        self.print_all_nodes(node.right)

    def remove(self, task):
        assert task.rb_node is not None, f"BUG: Task pid={task.pid} is not in the tree"
        #assert task.rb_node is None, f"BUG: Task pid={task.pid} was not properly removed from tree"
        parent = task.rb_node.parent
        self.delete_node(task.rb_node)
        # Fix min_vruntime:
        if parent:
            self.update_min_vruntime_up(parent)
        elif self.root:
            self.recompute_min_vruntime(self.root)

        # Think a little about this one.
        # Do not need to do it, since update_min_vruntime takes care of it.
        #if self.root is not None:
        #    self.cfs_rq.min_vruntime = self.root.task.min_vruntime
        #else:
        #    if not self.cfs_rq.curr or not self.cfs_rq.curr.on_rq:
        #        self.cfs_rq.min_vruntime = None


    def insert_min_vruntime(self, new_node):
        if new_node == self.root:
            return
        parent = new_node.parent
        while not parent == self.root:
            if new_node.min_vruntime < parent.min_vruntime:
                parent.min_vruntime = new_node.min_vruntime
            else:
                break
            parent = parent.parent

        if new_node.min_vruntime < parent.min_vruntime:
            parent.min_vruntime = new_node.min_vruntime

    def insert_node_iter(self, inserted_node, current):
        while True:
            if inserted_node.task.deadline > current.task.deadline:
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
        if next_node.task.deadline > inserted_node.task.deadline:
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
            if not grandparent:
                break  # Nothing more to fix if no grandparent exists
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

        # Fix min_vruntime after rotation
        self.recompute_min_vruntime(node)
        self.recompute_min_vruntime(new_parent)
        #Just to be on the safe side
        if new_parent.parent:
            self.update_min_vruntime_up(new_parent.parent)
        else:
            self.recompute_min_vruntime(self.root)

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

        # Fix min_vruntime after rotation
        self.recompute_min_vruntime(node)
        self.recompute_min_vruntime(new_parent)
        # Just to be on the safe side
        if new_parent.parent:
            self.update_min_vruntime_up(new_parent.parent)
        else:
            self.recompute_min_vruntime(self.root)

    def delete(self, value):
        node = self.find_node(self.root, value)
        if node is None:
            return  # Node not found

        self.delete_node(node)

    def delete_node(self, node):
        task = node.task  # this is the task we want to remove

        if node.left and node.right:
            successor = self.get_min(node.right)

            # Step 1: Store color before anything:
            deleted_black = (successor.color == self.BLACK)  # store color before anything

            # Store the hole location before it's overwritten
            fix_node_right = successor.right
            fix_node_parent = successor if successor.parent == node else successor.parent

            # Step 2: Fix successor’s parent pointer to bypass successor
            # If successor had a right child, it replaces successor in its original position
            if successor.parent != node:
                self.replace_node(successor, successor.right)
                successor.right = node.right
                if successor.right:
                    successor.right.parent = successor

            self.replace_node(node, successor)

            # Fix: reattach children
            successor.left = node.left
            # Not sure if we need to do this again.
            if successor.left is not None:
                successor.left.parent = successor

            #  If we removed a black node, we need to rebalance
            fix_from = fix_node_right if fix_node_right else fix_node_parent
            if deleted_black:
                self.fix_delete(fix_from)

            # We’re done, skip the rest
            task.rb_node = None
            node.task = None
            return

        child = node.left if node.left else node.right

        if child is not None:
            self.replace_node(node, child)
            if node.color == self.BLACK:
                self.fix_delete(child)
        else:
            if node.color == self.BLACK:
                self.fix_delete(node)
            self.replace_node(node, None)

        # Final pointer cleanup
        task.rb_node = None
        node.task = None

    # def delete_node(self, node):
    #     task = node.task  # Save the task for cleanup
    #
    #     # Case 1: Two children — replace node with its successor node
    #     if node.left is not None and node.right is not None:
    #         successor = self.get_min(node.right)
    #         self.transplant_node_data(node, successor)
    #         node = successor  # Now delete successor instead
    #
    #     # Now node has at most one child
    #     child = node.left if node.left else node.right
    #
    #     if child:
    #         self.replace_node(node, child)
    #         if node.color == self.BLACK:
    #             self.fix_delete(child)
    #     else:
    #         if node.color == self.BLACK:
    #             self.fix_delete(node)
    #         self.replace_node(node, None)
    #
    #     #TODO: Not sure if this is right yet.
    #     # Final cleanup
    #     node.task.rb_node = None
    #     #node.task = None
    #
    # def transplant_node_data(self, target_node, from_node):
    #     """
    #     Copy only the RB-tree-related values from from_node into target_node.
    #     This keeps the task identity intact.
    #     """
    #     target_node.task = from_node.task
    #     from_node.task.rb_node = from_node  # Update task pointer to new node
    #     target_node.task.rb_node = target_node  # Point task to its new place

    # def delete_node(self, node):
    #     # If node has two children, find successor and swap values
    #     if node.left is not None and node.right is not None:
    #         successor = self.get_min(node.right)
    #         node.task, successor.task = successor.task, node.task
    #         #node.task.deadline = successor.task.deadline
    #         node = successor  # Delete successor instead
    #
    #     # Node now has at most one child
    #     child = node.left if node.left else node.right
    #
    #     if child:  # If node has one child, replace it
    #         self.replace_node(node, child)
    #         if node.color == self.BLACK:
    #             self.fix_delete(child)
    #     else:  # If node has no children
    #         if node.color == self.BLACK:
    #             self.fix_delete(node)
    #         self.replace_node(node, None)
    #
    #     node.task.rb_node = None

    def fix_delete(self, node):
        while node != self.root and node.color == self.BLACK:
            if not node.parent:
                break
            if node == node.parent.left:
                sibling = node.parent.right
                if sibling and sibling.color == self.RED:  # Case 1: Sibling is RED
                    sibling.color = self.BLACK
                    node.parent.color = self.RED
                    self.rotate_left(node.parent)
                    sibling = node.parent.right

                if sibling is not None and \
                        (sibling.left is None or sibling.left.color == self.BLACK) and \
                        (sibling.right is None or sibling.right.color == self.BLACK):  # Case 2: Sibling's children are BLACK
                    sibling.color = self.RED
                    node = node.parent
                else:
                    if sibling is not None and (sibling.right is None or sibling.right.color == self.BLACK):  # Case 3: Sibling's right child is BLACK
                        if sibling.left:
                            sibling.left.color = self.BLACK
                        sibling.color = self.RED
                        self.rotate_right(sibling)
                        sibling = node.parent.right

                    # Case 4: Sibling's right child is RED
                    if sibling is not None:
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

                if sibling is not None and \
                        (sibling.left is None or sibling.left.color == self.BLACK) and \
                        (sibling.right is None or sibling.right.color == self.BLACK):
                    sibling.color = self.RED
                    node = node.parent
                else:
                    if sibling is not None and (sibling.left is None or sibling.left.color == self.BLACK):
                        if sibling.right:
                            sibling.right.color = self.BLACK
                        sibling.color = self.RED
                        self.rotate_left(sibling)
                        sibling = node.parent.left

                    if sibling is not None:
                        sibling.color = node.parent.color
                        node.parent.color = self.BLACK
                        if sibling.left:
                            sibling.left.color = self.BLACK
                        self.rotate_right(node.parent)
                    node = self.root

        node.color = self.BLACK  # Ensure node is black


    def find_node(self, root, value):
        if root is None or root.task.deadline == value:
            return root
        if value < root.task.deadline:
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
        if new_node is not None:
            new_node.parent = node.parent

    def get_next_process(self):
        node = self.root
        while node.left is not None:
            node = node.left

        # this deletes the node, be careful
        self.delete_node(node)
        return node.task

    def pick_first_entity(self):
        if self.root is None:
            print("tree is empty")
            return None
        node = self.root
        while node.left is not None:
            node = node.left

        return node.task

    def print_tree(self, node=None, indent="", last=True):
        if node is None:
            node = self.root
            if node is None:
                print("(empty tree)")
                return

        print(indent, "`- " if last else "|- ",
              f"[{'R' if node.color else 'B'}] "
              f"pid={node.task.pid}, "
              f"deadline_task={node.task.deadline}, "
              f"vruntime={node.task.vruntime}, "
              f"min_vruntime={node.min_vruntime}", sep="")
        indent += "   " if last else "|  "

        if node.left or node.right:
            if node.left:
                self.print_tree(node.left, indent, False)
            else:
                print(indent + "|- (None)")

            if node.right:
                self.print_tree(node.right, indent, True)
            else:
                print(indent + "`- (None)")






