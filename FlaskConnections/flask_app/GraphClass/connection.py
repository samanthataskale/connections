from GraphClass.edge_color import EdgeColor

class Connection:
    """Class for a connection. This will be extended for when
    a new type is added. (work or familial relationships, etc.)"""

    def __init__(self):
        """Constructor for a connection must be implemented by subclass."""
        self.name = ""
        pass

    def getName(self):
        """Simple getter for the work's name"""
        return self.name

    def getColor(self):
        """Simple getter for what the connection color should be."""
        pass

    def __eq__(self, other):
        """Determines equality between connections. It is based on connection title"""
        return self.name[0] == other.name[0]
    
class Work(Connection):
    """Class for a work that extends Connection. Has additional
    instance variables and the compareTo method is based on the date."""

    def __init__(self, title, date, authors, topic):
        """Constructor for a work. A date is a tuple of three ints."""
        self.name = title
        self.date = date # ex: (1, 22, 2020) is January 22, 2020
        self.authors = authors
        self.topic = topic

    def setAuthors(self, authors):
        """Simple setter for authors if added after initialization."""
        self.authors = authors

    def getColor(self):
        """Simple getter for what the connection color should be."""
        pass
    
class Patent(Work):
    """Class for a patent. Allows for customization for just patents."""

    def getColor(self):
        """Simple getter for what the connection color should be."""
        return EdgeColor.PATENT

    def __json__(self):
        return self.__dict__
class Patent(Work):
    """Class for a patent. Allows for customization for just patents."""

    def getColor(self):
        """Simple getter for what the connection color should be."""
        return EdgeColor.PATENT

    def __json__(self):
        return self.__dict__

class Publication(Work):
    """Class for a publication. Allows for customization for
    just publications."""
    def __json__(self):
        return self.__dict__

    def getColor(self):
        """Simple getter for what the connection color should be."""
        return EdgeColor.PUBLICATION
class Publication(Work):
    """Class for a publication. Allows for customization for
    just publications."""
    def __json__(self):
        return self.__dict__

    def getColor(self):
        """Simple getter for what the connection color should be."""
        return EdgeColor.PUBLICATION