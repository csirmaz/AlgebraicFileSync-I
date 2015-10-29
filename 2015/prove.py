

# Constants for Content.type:
DIR   = ' Dir'
FILE  = 'File'
EMPTY = 'Empty'


class Content:
    """Represents some content (value) at a given filesystem node
    
    Private properties:
        type (enum): DIR or FILE or EMPTY
        value (str): an arbitrary string representing the contents
        
    """

    def __init__(self, type=EMPTY, value='Unknown'):
        """Constructor
        
        Args:
            type (Optional[enum]): DIR or FILE or EMPTY
            value (Optional[str]): an arbitrary string representing the contents
        
        """
        self.type = type
        self.value = value
        
    def clone(self):
        """Returns a deep clone of the object."""
        return self.__class__(self.type, self.value)

    def info(self, addvalue=True):
        """Returns human-readable information about the object.
        
        Args:
            addvalue (Optional[bool]): whether to add the value to the output
            
        Returns:
            str
            
        """
        r = self.type
        if not self.isEmpty() and addvalue: r += "(" + self.value + ")"
        return r
        
    def isSame(self, content):
        """Returns whether the current object is the same as another instance of Content."""
        return (self.type == content.type and self.value == content.value)
        
    def getType(self):
        return self.type
    
    def getValue(self):
        if self.isEmpty(): return 'Unknown'
        return self.value
        
    def isDir(self):
        """Returns whether the type of the object is 'diretory'."""
        return (self.type == DIR)

    def isFile(self):
        """Returns whether the type of the object is 'file'."""
        return (self.type == FILE)

    def isEmpty(self):
        """Returns whether the type of the object is 'empty'."""
        return (self.type == EMPTY)


def ContentFactory(value='Unknown'):
    """Generates all possible contents.
    
    Args:
        value (Optional[str]): the value of the content objects
        
    Yields:
        All possible content objects
        
    """
    yield Content(EMPTY)
    yield Content(FILE, value)
    yield Content(DIR, value)


class Node:
    """Represents a path and its environment relevant for commands
    
    has_parent = bool
    content = Content object
    has_child = bool
    broken = None or string if broken (the reason for being broken)
    """

    def __init__(self, has_parent=False, content=None, has_child=False, broken=False):
        self.has_parent = has_parent
        self.content = Content() if content is None else content
        self.has_child = has_child
        self.broken = 'Constructor' if broken else None
        self.checkTreeProperty()
        
    def clone(self):
        return self.__class__(self.has_parent, self.content.clone(), self.has_child, self.broken)
        
    def info(self, debug=False):
        """Returns human-readable information about the object"""
        r = []
        if self.isBroken():
            if debug:
                r.append("Broken(" + self.broken + ") ")
            else:
                return "(Broken)"
        if self.has_parent: r.append("o--")
        r.append(self.content.info())
        if self.has_child: r.append("--o")
        return "(" + "".join(r) + ")"
        
    def isSame(self, node):
        if self.isBroken() and node.isBroken(): return True
        if self.isBroken() or node.isBroken(): return False
        return (self.has_parent == node.has_parent and self.content.isSame(node.content) and self.has_child == node.has_child)

    def isBroken(self):
        return not self.broken is None
        
    def setBroken(self, reason='unknown'):
        self.broken = reason
        return self

    def getContent(self):
        return self.content
        
    def setContent(self, content):
        self.content = content
        self.checkTreeProperty()
        return self
        
    def setHasChild(self, v):
        self.has_child = v
        self.checkTreeProperty()
        return self
        
    def setHasParent(self, v):
        self.has_parent = v
        self.checkTreeProperty()
        return self
        
    def checkTreeProperty(self):
        """Break the node if there is a contradiction between the flags (environment) and the contents"""
        if not self.content.isEmpty() and not self.has_parent:
            self.broken = 'tree-nonempty-noparent'
        if self.has_child and not self.content.isDir():
            self.broken = 'tree-notdir-haschild'
        return self
        
    def assertDescendant(self):
        """Break the node if it does not have descendants"""
        # print "assert child on " + self.info()
        if not self.has_child or not self.content.isDir():
            self.broken = 'assert-child'
        return self
        
    def assertNoDescendants(self):
        """Break the node if it has any descendants"""
        # print "assert no child on " + self.info()
        if self.has_child:
            self.broken = 'assert-no-child'
        return self
        
    def assertParent(self):
        """Break the node if it has no parent"""
        # print "assert parent on " + self.info()
        if not self.has_parent:
            self.broken = 'assert-parent'
        return self
        
    def assertNoParent(self):
        """Break the node if it has a parent"""
        # print "assert no parent on " + self.info()
        if self.has_parent:
            self.broken = 'assert-no-parent'
        return self


def NodeFactory(value='Unknown'):
    """Generator for all possible nodes"""
    yield Node(broken=True)
    for has_parent in [False, True]:
        for content in ContentFactory(value):
            for has_child in [False, True]:
                node = Node(has_parent, content, has_child)
                if not node.isBroken():
                    yield node


# Constants for Filesystem.rel:
DIRECT_PARENT      = 'DirectParent'      # p2 is the parent of p1
DIRECT_PARENT_ONLY = 'DirectParentOnly'  # p2 is the parent of p1 and p1 is the only child
DIRECT_CHILD       = 'DirectChild'       # p2 is the child of p2
DIRECT_CHILD_ONLY  = 'DirectChildOnly'   # p2 is the child of p1 and p2 is the only child
SEPARATE           = 'Separate'          # all other cases

SAME               = 'Same'              # two paths are the same (used for command pairs)

class Filesystem:
    """Models a filesystem focusing on two paths to emulate the results of commands
    
    p1 = Node object
    p2 = Node object
    rel = DIRECT_PARENT or DIRECT_PARENT_ONLY or DIRECT_CHILD or DIRECT_CHILD_ONLY or SEPARATE
    """
    
    def __init__(self, p1, p2, rel):
        self.p1 = p1
        self.p2 = p2
        self.rel = rel
        self.checkTreeProperty()
        
    def info(self, debug=False):
        """Returns human-readable information about the object"""
        if self.isBroken() and not debug:
            return "[Broken]"
        if self.rel == SEPARATE:
            return self.p1.info(debug) + " ==x== " + self.p2.info(debug)
        if self.rel == DIRECT_CHILD:
            return self.p1.info(debug) + " ===<> " + self.p2.info(debug)
        if self.rel == DIRECT_CHILD_ONLY:
            return self.p1.info(debug) + " ===>> " + self.p2.info(debug)
        if self.rel == DIRECT_PARENT:
            return self.p2.info(debug) + " ~~~<> " + self.p1.info(debug)
        if self.rel == DIRECT_PARENT_ONLY:
            return self.p2.info(debug) + " ~~~>> " + self.p1.info(debug)
    
    def clone(self):
        return self.__class__(self.p1.clone(), self.p2.clone(), self.rel)
        
    def isSame(self, fs):
        if self.isBroken() and fs.isBroken(): return True
        if self.isBroken() or fs.isBroken(): return False
        return (self.p1.isSame(fs.p1) and self.p2.isSame(fs.p2) and self.rel == fs.rel)
        
    def isExtendedBy(self, fs):
        """Returns true if self is broken but fs is not, or the are the same"""
        if self.isBroken(): return True
        if fs.isBroken(): return False
        return (self.p1.isSame(fs.p1) and self.p2.isSame(fs.p2) and self.rel == fs.rel)
    
    def isBroken(self):
        return (self.p1.isBroken() or self.p2.isBroken())
        
    def checkTreeProperty(self):
        """Break nodes if their flags contradict the relationship between the paths"""
        if self.rel == SEPARATE:
            return self

        if self.rel in [DIRECT_CHILD, DIRECT_CHILD_ONLY]:
            parent = self.p1
            child = self.p2
        else:
            parent = self.p2
            child = self.p1
            
        only = self.rel in [DIRECT_CHILD_ONLY, DIRECT_PARENT_ONLY]
    
        if not child.getContent().isEmpty():
            # print "child not empty"
            parent.assertDescendant()

        if not parent.getContent().isEmpty():
            # print "parent not empty"
            child.assertParent()
        else:
            # print "parent empty"
            child.assertNoParent()

        if only and child.getContent().isEmpty():
            # print "only child and child empty"
            parent.assertNoDescendants()
            
            
    def applyCommand(self, command):

        command_path = command.getPath()
        new_content = command.getEnd()

        # If we apply a command to the (direct) child path,
        # then we may need to update the has_child flag of the parent
        if self.rel != SEPARATE:
            if self.rel in [DIRECT_CHILD, DIRECT_CHILD_ONLY]:
                childpath = PATH2
                child = self.p2
                parentpath = PATH1
                parent = self.p1
            else:
                childpath = PATH1
                child = self.p1
                parentpath = PATH2
                parent = self.p2                

            if command_path == childpath:
                
                # If the child will have content, the parent will have a child
                if not new_content.isEmpty():
                    parent.setHasChild(True)
                
                # If the only child is deleted, the parent will have no child
                if self.rel in [DIRECT_CHILD_ONLY, DIRECT_PARENT_ONLY] and new_content.isEmpty():
                    parent.setHasChild(False)
                    
            if command_path == parentpath:
            
                # If the parent is deleted, the child will have no parent
                if new_content.isEmpty():
                    child.setHasParent(False)
                
                # If the parent is created, the child will have a parent
                else:
                    child.setHasParent(True)
  
        # Here the command is always applied to a different path than the one we changed above
        command.applyToNode(self.p1 if command_path == PATH1 else self.p2)
            
        return self
        
    def applySequence(self, sequence):
        sequence.map(lambda x: self.applyCommand(x))


def FilesystemFactory(rel):
    yield Filesystem(Node(broken=True), Node(broken=True), rel)
    for p1_source in NodeFactory('Old1'):
        for p2 in NodeFactory('Old2'):
            fs = Filesystem(p1_source.clone(), p2, rel)  # the constructor may break the p1 node, so we need to clone
            if not fs.isBroken():
                yield fs


# Constants for Command.path:
PATH1 = 'P1'
PATH2 = 'P2'


class Command:
    """Represents a command

    path - PATH1 or PATH2
    start - a Content object (the value is disregarded)
    end - a Content object
    """
    
    def __init__(self, path, start, end):
        self.path = path
        self.start = start
        self.end = end
        
    def info(self, debug=False):
        """Returns human-readable information about the object"""
        return "{" + self.path + ":" + self.start.info(False) + ">" + self.end.info() + "}"

    def getPath(self):        
        return self.path
        
    def getEnd(self):
        return self.end

    def applyToNode(self, node):
        """Apply the command to a node"""
        if node.getContent().getType() != self.start.getType():
            node.setBroken('command-start')
            return self
        node.setContent(self.end)
        return self


def CommandFactory(path, value):
    for c1 in ContentFactory('N/A'):
        for c2 in ContentFactory(value):
            yield Command(path, c1, c2)


class Sequence:
    """Represents a command sequence
    
    commands - a list of Command objects
    """
    
    def __init__(self, commands):
        self.commands = commands
        
    def info(self, debug=False):
        """Returns human-readable information about the object"""
        return "; ".join(map(lambda x: x.info(debug), self.commands))
        
    def clone(self):
        return self.__class__(self.commands[:])
        
    def getReverse(self):
        tmp = self.clone()
        tmp.commands.reverse()
        return tmp
        
    def map(self, func):
        return map(func, self.commands)



class CommandPair(Sequence):
    """ Represents a pair of commands
   
    see parent class
    rel = DIRECT_PARENT or DIRECT_PARENT_ONLY or DIRECT_CHILD or DIRECT_CHILD_ONLY or SEPARATE or SAME
    """
    # There is no need to consider any other relationship, e.g. when one path is a parent,
    # but not a direct parent of the other one, as unless there is a direct relationship,
    # the command on one path is not going to change the environment of the other.

    def __init__(self, command1, command2, rel):
        self.commands = [command1, command2]
        self.rel = rel
        
    def info(self, debug=False):
        """Returns human-readable information about the object"""
        if self.rel == SEPARATE:
            return self.commands[0].info(debug) + " -x- " + self.commands[1].info(debug)
        if self.rel == DIRECT_CHILD:
            return self.commands[0].info(debug) + " -<> " + self.commands[1].info(debug)
        if self.rel == DIRECT_CHILD_ONLY:
            return self.commands[0].info(debug) + " ->> " + self.commands[1].info(debug)
        if self.rel == DIRECT_PARENT:
            return self.commands[0].info(debug) + " <>- " + self.commands[1].info(debug)
        if self.rel == DIRECT_PARENT_ONLY:
            return self.commands[0].info(debug) + " <<- " + self.commands[1].info(debug)
        if self.rel == SAME:
            return self.commands[0].info(debug) + " --- " + self.commands[1].info(debug)
        
    def clone(self):
        return self.__class__(self.commands[0], self.commands[1], self.rel)
        
    def getRelationship(self):
        return self.rel

    def getReverse(self):
        tmp = Sequence.getReverse(self)
        if self.rel == DIRECT_PARENT:
            tmp.rel = DIRECT_CHILD
        elif self.rel == DIRECT_PARENT_ONLY:
            tmp.rel = DIRECT_CHILD_ONLY
        elif self.rel == DIRECT_CHILD:
            tmp.rel = DIRECT_PARENT
        elif self.rel == DIRECT_CHILD_ONLY:
            tmp.rel = DIRECT_PARENT_ONLY
        return tmp
    
    def getLast(self):
        return self.commands[1]


def CommandPairFactory():
    """Constructs all 2-long command sequences"""
    for rel in [SEPARATE, DIRECT_CHILD, DIRECT_CHILD_ONLY, DIRECT_PARENT, DIRECT_PARENT_ONLY]:
        for c1 in CommandFactory(PATH1, 'New1'):
            for c2 in CommandFactory(PATH2, 'New2'):
                yield CommandPair(c1, c2, rel)
    for c1 in CommandFactory(PATH1, 'New1'):
        for c2 in CommandFactory(PATH1, 'New2'):
            yield CommandPair(c1, c2, SAME);

# We test command pairs and aim to answer the following questions:
# - Will the pair break all filesystems?
# - If not, can the pair be substituted by a single command?
# - If not, can the pair be reversed?
# We are also interested in substitutions that extend the domain of the sequence.

for sq in CommandPairFactory():

    fs_rel = sq.getRelationship()
    if fs_rel == SAME:
        fs_rel = SEPARATE
        
    # Does it break all filesystems?
    for fs in FilesystemFactory(fs_rel):
        fs.applySequence(sq)
        if not fs.isBroken():
            break # Skips "else" below
    else: # If none is broken
        print sq.info() + " \t== break"
        continue

    # Try to find a single command with the same effect
    # We know this is only possible, if the pair does not break all filesystems,
    # if the two commands affect the same path.
    canSimplify = False
    if sq.getRelationship() == SAME:
        for command in CommandFactory(sq.getLast().getPath(), sq.getLast().getEnd().getValue()):
            simplifiesEq = True  # Whether command is equivalent to sq on all filesystems
            simplifiesExt = True # Whether command extends sq
            for fs in FilesystemFactory(fs_rel):
                # Apply the original sequence
                fs_res = fs.clone()
                fs_res.applySequence(sq)
                # Apply the single command
                fs_single = fs.clone()
                fs_single.applyCommand(command)
                if not fs_res.isSame(fs_single): simplifiesEq = False
                if not fs_res.isExtendedBy(fs_single): simplifiesExt = False
            if simplifiesEq:
                canSimplify = True
                print sq.info() + " \t== " + command.info()
            elif simplifiesExt:
                canSimplify = True
                print sq.info() + " \t=[ " + command.info()
    
    if canSimplify: continue

    # Reverse sequence
    sq_rev = sq.getReverse()
    # print sq_rev.info()
    
    reverseEq = True
    reverseExt = True

    for fs in FilesystemFactory(fs_rel):
        # Apply the original sequence
        fs_res = fs.clone()
        fs_res.applySequence(sq)
        # Apply the reverse sequence
        fs_rev_res = fs.clone()
        fs_rev_res.applySequence(sq_rev)
        if not fs_res.isSame(fs_rev_res): reverseEq = False
        if not fs_res.isExtendedBy(fs_rev_res): reverseExt = False
    if reverseEq:
        print sq.info() + " \t== " + sq_rev.info()
        continue
    if reverseExt:
        print sq.info() + " \t=[ " + sq_rev.info()
        continue
    
    print sq.info() + " \t(no rule)"
