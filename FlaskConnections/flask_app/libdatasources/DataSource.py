#comments will explain how to add a new datasource to each class
class DataSource(object):
    # This gives the display name of the datasource as a string
    source = ""
    # This states whether or not the datasource has support for aliases - ie, more than one "name" per id
    aliases = False

    #returns a map with name, first seen, last seen, and the original ID if it exists in the database
    #returns None if the ID is incorrect, yields no results, or if an error occurs during fetching
    #Used when trying to get a display name when the id input method was used
    @classmethod
    def get_name_from_id(cls, sourceId):
        return None

    #a simplified version of get_name_from_id
    #Return True if the ID is valid for the datasource, False if not
    #Used to verify user-inputted IDs
    @classmethod
    def check_id(cls, sourceid):
        return False

    #takes in a name
    #return True if the some entry with the name exists in the datasource
    #return False otherwise
    #Used to verify that a user-inputted name is valid
    @classmethod
    def check_name(cls, name):
        return False

    #takes in a list of names
    #returns a list of possible authors based on the names. If more than one is found, for each entry, return
    #mandatory: sourceId, name, first_seen, last_seen, and aliases if class.aliases = True
    #optional: any other identifying information needed
    #will return an empty list [] if nothing was found
    #Used for author disambiguation - both from initial name input and for steps beyond the first one
    @classmethod
    def get_disamb_from_name(cls, names):
        return []

    #This is a static method, used for all datasources, that removes duplicate entries
    #Does not need to be implemented by child classes
    @classmethod
    def remove_duplicate(cls, people):
        new_list = []
        added_ids = []
        for item in people:
            if item["sourceId"] not in added_ids:
                added_ids.append(item["sourceId"])
                new_list.append(item)
        return new_list