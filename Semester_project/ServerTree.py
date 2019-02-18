#!/usr/bin/env python3


class Tree:

    rootNode = None

    connectionQueue = []

    # True if a new queue list made by all of Root's child must be made.
    # Usually used only for the first few connections (5).
    connectingToRoot = True

    class Node:
        parentNode = None

        HostInstance = None

        firstChild = None
        secondChild = None
        thirdChild = None
        fourthChild = None
        fifthChild = None

        childCounter = 0  # From 0 to 5. 5 means the Node is full.
        siblingCounter = None  # From 1 (first child) to 5 (last child)

        def __init__(self, parent, host, siblingCounter=1):
            self.parentNode = parent
            self.HostInstance = host
            self.siblingCounter = siblingCounter

        def getNode(self, value=-1):
            switcher = {
                -1: self.parentNode,
                0: self,
                1: self.firstChild,
                2: self.secondChild,
                3: self.thirdChild,
                4: self.fourthChild,
                5: self.fifthChild}
            return switcher[value]

        def getHost(self):
            return self.HostInstance

        def getChildCounter(self):
            return self.childCounter

        def increaseChildCounter(self, amount=1):
            self.childCounter += amount

    def __init__(self, host):
        self.startingNode = Node(None, host)
        self.rootNode = startingNode
        self.connectionQueue.append(self.startingNode)

    def addHost(self, host):
        currentNode = self.connectionQueue.pop()
        currentNodeNewChildCount = currentNode.getChildCounter() + 1
        newNode = Node(currentNode, newNode, currentNodeNewChildCount)
        currentNode.increaseChildCounter()
        if currentNodeNewChildCount < 5:
            self.connectionQueue.append(currentNode)
        else:
            if self.connectingToRoot:
                for i in range(1, 6):
                    self.connectionQueue.append(currentNode.getNode(i))
                else:
                    self.connectingToRoot = False
            # Be REALLY carefull: if the host disconnection is not good, this
            # will cause a lot of problems later, and won't work as intended.
            self.connectionQueue.append(currentNode.getNode(1))