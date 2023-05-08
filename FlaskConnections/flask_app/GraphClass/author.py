from GraphClass import IDConstants
import json

class Author:
    """This class stores the author information. An author has an ID, a list of works, and a name.
    The name is the alias with the most information. The list of works is ordered for getting the
    timeline of an author."""

    def __init__(self, IDs, name, works):
        """Constructor that sets an author's information. The ID is a tuple of all database ids
        (when one is added, the programmer should add another id to the tuple in the data collection.
        If a database is not used, like when searching just patents, a -1 should be entered. For example,
        (semantic scholar ID, patent ID, -1) if you have 3 databases and are only using the first two).
        """
        if (len(IDs) != IDConstants.NUM_DATABASES):
            raise Exception("Need a placeholder ID for each database not used!")

        self.IDs = IDs # Note that the ID is tuple of ids from each database
        self.works = works # must be ordered by date
        self.works = sorted(works, key = lambda x : x.date)
        # name of the author that is the alias that provides
        #the most information
        self.name = name
        # confidence interval that an id for a database is accurate
        self.confidenceInterval = (100, 50)

    def __json__(self):
        return self.__dict__

    def getWorks(self):
        """Simple getter for all the author's works in order by date."""
        return self.works

    def addWorks(self, work: list):
        """Just in case a work is found after an author is made, this is a way to add an
        additional work."""
        self.works + work
        self.works.sort(key = lambda x : x.date) # must remain sorted

    def getIds(self):
        """Simple getter for the author's IDs."""
        return self.IDs

    def setIds(self, newIDForOneDatabase, databasePosition):
        """Simple setter for the author's ID. Add an ID to a specific
        pos for a given database id"""
        oldIDs = self.IDs
        oldIDs = list(oldIDs)
        oldIDs[databasePosition] = newIDForOneDatabase
        self.IDs = tuple(oldIDs)

    def getName(self):
        return self.name

    def getConfidence(self, databasePos : int):
        """Returns the confidence interval that a database id actually represents the
        right author."""
        return self.confidenceInterval[databasePos]

    def __eq__(self, other):
        """Determines equality between authors. It is based on ID"""
        return self.IDs[0] == other.IDs[0]

    def __repr__(self):
        """Method to print object using author name"""
        return json.dumps({"IDs": self.IDs, "works": self.works, "name": self.name})

    def __hash__(self) -> int:
        return hash(self.IDs)