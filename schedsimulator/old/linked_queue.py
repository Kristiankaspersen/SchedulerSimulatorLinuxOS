class TheQueue:
    def __init__(self):
        self.tail = None  # out first
        self.head = None  # put in

    def pop(self):
        queue_head = None
        if self.empty():
            print("Empty")
        else:
            queue_head = self.head
            if self.head == self.tail:
                self.tail = self.head.next  # In this case self.head.next would be None. Meaning both head and tail would be None.
            self.head = self.head.next
        return queue_head

    def push(self, node):
        if self.empty():
            self.tail = node
            self.head = node
        else:
            self.tail.next = node
            self.tail = self.tail.next

    def empty(self):
        return self.tail is None and self.head is None

    # Making the queue iterable
    def __iter__(self):
        self._iter_node = self.head  # Start iteration from head
        return self

    def __next__(self):
        if self._iter_node is None:
            raise StopIteration
        value = self._iter_node.value
        self._iter_node = self._iter_node.next
        return value