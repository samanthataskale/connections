from GraphClass import IDConstants
from libdatasources.SemanticScholar import SemanticScholar
from libdatasources.PatentView import PatentView
from GraphClass.author import Author

def bulk_lookup(authors_dict: dict[any, Author], inventors_dict: dict[any, Author]):
    if len(authors_dict) == 0:
        return authors_dict

    # Look up all PatentsView inventors that we don't have
    names = set()
    for key, author in authors_dict.items():
        if author.getIds()[IDConstants.PUBLICATION] != SemanticScholar.skipid and author.getIds()[IDConstants.PUBLICATION] != IDConstants.NEED_ID:
            if author.getIds()[IDConstants.PATENT] == IDConstants.NEED_ID:
                names.add(author.getName())

    possible_names = PatentView.get_disamb_from_name(list(names))

    for key, author in authors_dict.items():
        if author.getIds()[IDConstants.PUBLICATION] != SemanticScholar.skipid and author.getIds()[IDConstants.PUBLICATION] != IDConstants.NEED_ID:
            if author.getIds()[IDConstants.PATENT] == IDConstants.NEED_ID:
                # Set the id to PatentView.skipid, will be overwritten if we do find a match
                author.setIds(PatentView.skipid, IDConstants.PATENT)
                
                for possible_name in possible_names:
                    # Just take first matching name
                    if author.getName() == possible_name["name"]:
                        author.setIds(possible_name["sourceId"], IDConstants.PATENT)
                        
                        # Copy it over into inventors_dict:
                        inventors_dict[author.getIds()[IDConstants.PATENT]] = author
                        id_found = True
                        break
                    
    # Rinse and repeat for SemanticScholar
    if len(inventors_dict) == 0:
        return inventors_dict
    
        # Look up all PatentsView inventors that we don't have
    names = set()
    for key, inventor in inventors_dict.items():
        if inventor.getIds()[IDConstants.PATENT] != PatentView.skipid and inventor.getIds()[IDConstants.PATENT] != IDConstants.NEED_ID:
            if inventor.getIds()[IDConstants.PUBLICATION] == IDConstants.NEED_ID:
                names.add(inventor.getName())


    possible_names = SemanticScholar.get_disamb_from_name(list(names))

    for key, inventor in inventors_dict.items():
        if inventor.getIds()[IDConstants.PATENT] != PatentView.skipid and inventor.getIds()[IDConstants.PATENT] != IDConstants.NEED_ID:
            if inventor.getIds()[IDConstants.PUBLICATION] == IDConstants.NEED_ID:
                # Set the id to SemanticScholar.skipid, will be overwritten if we do find a match
                inventor.setIds(SemanticScholar.skipid, IDConstants.PUBLICATION)
            
                for possible_name in possible_names:
                    # Just take first matching name
                    if inventor.getName() == possible_name["name"]:
                        inventor.setIds(possible_name["sourceId"], IDConstants.PUBLICATION)
                        
                        # Copy it over into authors_dict:
                        authors_dict[inventor.getIds()[IDConstants.PUBLICATION]] = inventor
                        break

    return authors_dict, inventors_dict