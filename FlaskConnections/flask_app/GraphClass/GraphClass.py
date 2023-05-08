# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 12:17:41 2023
@author: James Allen (reviewed by Theresa, Akash, and Eric)
This code was created for CMSC435 Team 01's Connections Project Spring 2023
"""

import networkx as nx
from pyvis.network import Network
import json_fix
import json
from libdatasources.SemanticScholar import SemanticScholar
from libdatasources.PatentView import PatentView
import random
from GraphClass import IDConstants
from GraphClass.author import Author
from GraphClass.connection import Patent, Publication
from libdatasources.find_in_other_databases import bulk_lookup
from networkx.readwrite import json_graph
from lookup_forms import lookup_classes

def compare_dates(date1, date2):
    if date2 is None or date1 is None:
        return False
    return date2 > date1


class Graph:
    """This class stores the initial author the graph is built around as the
    root node. It also has a name specified by the user. This data structure
    will store data for data visualization and exploratory tools. A
    visualization module will use instances of this class to display the data.
    """
    # colorLookup = {0: "#add8e6", 1: "#60d43d", 2: "#a93dd4", 3: "#d43d51"}
    # Constructor. Sets instance variables root in graph

    def __init__(self, *args):
        """ Constructor for the graph class. It builds a graph off of
         an existing graph or makes one off of an existing root node that
         should have no edges.
        """
        if (len(args) == 1 and isinstance(args[0], str)):
            pass
        elif (len(args) == 0):  # initialize new graph
            self.roots = [] # Multiple roots are possible now. Yay
            self.depths = [] # Multiple depths possible bc of multiple roots. Yay
            self.nxGraph = nx.MultiGraph(selfloops=False, multiedges=True)
            # will store the nodes that an author is in. Uses the author ID as the key
            self.lookupAuthor = {}
            self.deepestColor = ""
        else:
            raise Exception("Graph initialized incorrectly!")

    def from_json(graph_json: str):
        graph_dict = json.loads(graph_json)

        graph = Graph()
        graph.roots = graph_dict["name"]
        graph.depths = graph_dict["depths"]
        graph.nxGraph = json_graph.node_link_graph(graph_dict["nxGraph"])
        for nodeID, IDs in graph_dict["lookupAuthor"].items():
            graph.lookupAuthor[tuple(IDs)] = nodeID
        #print(graph.getNodes())
        return graph

    def to_json(self) -> str:
        graph_dict = {}
        graph_dict["name"] = self.roots
        graph_dict["depths"] = self.depths
        graph_dict["nxGraph"] = json_graph.node_link_data(self.nxGraph)

        lookupAuthor_dict = {}
        for IDs, nodeID in self.lookupAuthor.items():
            lookupAuthor_dict[nodeID] = {}
            for i, lookup_class in enumerate(lookup_classes):
                lookupAuthor_dict[nodeID][str(i)] = IDs[i]

        graph_dict["lookupAuthor"] = lookupAuthor_dict

        return json.dumps(graph_dict)
    
    def recolor_nodes(self):
        """Checks how far each node is from each root and colors it accordingly."""
        
        self.deepestColor = ""
        # Find shortest paths - this can be done more quickly I think, but this function does a good enough job for now
        shortest = dict(nx.all_pairs_shortest_path(self.nxGraph))
        colors = ["#e6bbad", "#add8e6", "#b9fc97", "#f9d781", "#dbb0fc"]
        
        for node in self.nxGraph.nodes:
            # Find the distances from this node to every root node
            path_lengths = [len(shortest[node][root]) for root in self.roots if root in shortest[node]]
            if len(path_lengths) == 0:
                shortest_path = 1 # Couldn't find anything. Set ourself as a root node equivalent
            else:
                shortest_path = min(path_lengths)
            
            self.nxGraph.nodes[node]["color"] = colors[min(shortest_path, len(colors)) - 1]

            if self.deepestColor == "" or colors.index(self.deepestColor) < min(shortest_path, len(colors)) - 1:
                self.deepestColor = colors[min(shortest_path, len(colors)) - 1]
                
    def recolor_edges(self):
        if len(self.roots) == 2 and nx.has_path(self.nxGraph, source=self.roots[0], target=self.roots[1]):
            shortest = nx.shortest_path(self.nxGraph, source=self.roots[0], target=self.roots[1], weight=None) # Ignore the weights
            
            # This will create a dictionary where each key is the edge we want to modify.
            # The edge is a tuple of the form (node1, node2, key), where the key is always zero (it would increase if there were multiple edges between the same two nodes)
            edgelist = {tuple(edge): {"color": "#bc42f5", "weight": "7"} for edge in zip(shortest[:-1], shortest[1:], [0]*len(shortest[0:-1]))}
            
            nx.set_edge_attributes(self.nxGraph, edgelist)

    def generateNodeID(self, authors: list[Author]):
        """ This class method generates a node's ID from a list of authors"""
        return hash(tuple(a.getIds() for a in authors))

    def getNodeCount(self):
        """Returns the number of nodes in the networkx graph."""
        return self.nxGraph.number_of_nodes()

    def getNodes(self):
        """Returns the nodes in the networkx graph."""
        return self.nxGraph.nodes(data=True)

    def deleteNodeHelper(self, nodeID):
        """Delete node Helper"""

        #Updates author lookup table for authors in deleted node
        deletedKeys = []
        for key in self.lookupAuthor:
            if self.lookupAuthor[key] == nodeID:
                deletedKeys.append(key)

        for key in deletedKeys:
            if self.lookupAuthor[key] in self.roots:
                self.roots.remove(self.lookupAuthor[key])

            self.lookupAuthor.pop(key)

        # actually deletes node from the graph
        self.nxGraph.remove_node(nodeID)

    def deleteNode(self, id):
        """Deletes node which contains the author with an ID of id"""

        # get ID of the node to delete
        nodeID = self.lookupAuthor[tuple(id)]
        
        self.deleteNodeHelper(nodeID)
        self.recolor_nodes()
        self.recolor_edges()

        # Deletes all nodes which have no edges
        isolatedNodes = []
        for node in nx.isolates(self.nxGraph):
            isolatedNodes.append(node)

        for node in isolatedNodes:
            self.deleteNodeHelper(node)

    def splitNode(self, nodeID: int, auth: Author) -> list:
        """This function splits an existing node by removing an author and adding a node for it at the
        same depth of the existing node. """

        if (not (auth.getIds() in self.lookupAuthor)):
            raise Exception("I can only split an existing node!")
        else:
            # if the author to remove is in a node with only itself then no need to split
            authors = self.nxGraph.nodes(data=True)[nodeID]['auths']
            oldNodeExpanded = self.nxGraph.nodes(data=True)[nodeID]['expanded']

            if (len(authors) == 1):
                return [nodeID]
            else:
                # the author should be removed and placed in its own node

                # remove the author from this node and change the node id
                # (if the author is not in the list for some reason nothing happens)

                index = 0
                for a in authors:
                    if auth.IDs == a.IDs:
                        authors.pop(index)
                    index = index + 1

                # generate node id for split node
                splitNodeID = self.generateNodeID(authors)
                # update lookup
                for a in authors:
                    self.lookupAuthor[a.getIds()] = splitNodeID

                # generate id for node with one author
                newNodeID = self.generateNodeID([auth])
                # update lookup
                self.lookupAuthor[auth.getIds()] = newNodeID

                # make new nodes:
                index = 0
                authorStr = ""
                for a in authors:
                    if index == 0:
                        authorStr += a.name
                    else:
                        authorStr += ",\n" + a.name
                    index = index + 1


                color = self.nxGraph.nodes[nodeID]['color']

                self.nxGraph.add_node(
                    splitNodeID, auths=authors, label=authorStr, title = authorStr, shape="circle", color=color, expanded=oldNodeExpanded)
                self.nxGraph.add_node(
                    newNodeID, auths=[auth], label=auth.name, title = auth.name, shape="circle", color=color, expanded=oldNodeExpanded)

                # for every edge in the networkx graph incident to node, those edges should go to the
                # split and new nodes
                edges = self.nxGraph.edges([nodeID], data=True)

                # for each edge connecting to the old graph there should be two copies each connecting to
                # the new nodes (splitNodeId and newNodeID)
                for edge in edges:
                    # copy the edge twice (make sure from id is not the original node)
                    self.addEdge(
                        edge[0] if edge[0] != nodeID else edge[1], splitNodeID, edge[2]['conns'])
                    self.addEdge(
                        edge[0] if edge[0] != nodeID else edge[1], newNodeID, edge[2]['conns'])
                    
                    # add edge between split node and new node
                    self.addEdge(newNodeID, splitNodeID, edge[2]['conns'])

                # delete the old node (this deletes the original edges too)
                self.nxGraph.remove_node(nodeID)


                return [newNodeID]  # change this

    def addNodeHelper(self, currAuthor: Author, currIndex: int, authors: list[Author]) -> list:
        """ Recursive helper for addNode that breaks nodes when needed."""
        # recursively make nodes until
        if (len(authors) == 0):
            return []

        # generate nodeID from authorIDs
        nodeID = self.generateNodeID(authors)

        # if a group of the authors exists already
        if (self.nxGraph.has_node(nodeID)):
            return [nodeID]
        else:
            if currAuthor.getIds() in self.lookupAuthor:
                # if author is in another node then we will add an edge to an existing node
                # and whatever nodes are created by the rest of the authors
                index = 0
                for a in authors:
                    if currAuthor.IDs == a.IDs:
                        authors.pop(index)
                    index = index + 1

                newNodeID = self.lookupAuthor[currAuthor.getIds()]
                # need to split existing node if author is still in a group
                # will get an error for index out of range if last author is what is removed
                if (currIndex < len(authors)):
                    return self.splitNode(newNodeID, currAuthor) + self.addNodeHelper(authors[currIndex], currIndex, authors)
                else:
                    return self.splitNode(newNodeID, currAuthor)
            else:
                # author is not in another node so check the next author
                if (currIndex >= len(authors) - 1):
                    # there are no authors in another node. Thus, a new node must be made.

                    index = 0
                    authorStr = ""
                    for a in authors:
                        if index == 0:
                            authorStr += a.name
                        else:
                            authorStr += ",\n" + a.name
                        index = index + 1

                    
                    self.nxGraph.add_node(nodeID, auths=authors, label=authorStr, title = authorStr, shape="circle", color="#e6bbad", expanded=False)
                    
                    # update lookup table
                    for a in authors:
                        self.lookupAuthor[a.getIds()] = nodeID
                    return [nodeID]
                else:
                    # the current author is not already in the graph but the next one might be
                    currIndex = currIndex + 1
                    return self.addNodeHelper(authors[currIndex], currIndex, authors)

    def addNode(self, authors: list[Author]):
        a = authors
        """Adds a node to the networkx graph given a list of authors in the node and a node ID."""
        if (len(authors) > 0 and len(authors) <= 10):
            return self.addNodeHelper(authors[0], 0, authors)
        elif len(authors) > 10:
            t_ret = []
            while len(authors) > 10:
                t_ret.append(self.addNode(authors[:10]))
                authors = authors[10:]

            if len(authors) > 0:
                t_ret.append(self.addNode(authors))
            
            flat_list = [i for sublist in t_ret for i in sublist]
            
            return flat_list
        else:
            raise Exception("Cannot make an empty node.")

    def addEdge(self, ID1: int, ID2: int, connections: list):
        """After a node is created, the connection between nodes is added right after. To do this,
        the node ids connected are needed as well as the list of connection objects. The weight is
        always one, so we can use networkx functions. If the edge (id1,id2 matches) already exists, then
        a new edge is made only if the existing edge has a different connection type. """
        if (len(connections) == 0):
            raise Exception("Need at least one connection!")
        elif (ID1 in self.nxGraph and ID2 in self.nxGraph):
            # check that an edge with the same ids don't exist already if it does, only create another edge if different connection type
            if (ID1 != ID2):  # no self-loops
                notAdded = True
                if (ID1 in self.nxGraph and ID2 in self.nxGraph[ID1]):
                    # all edges between nodes as dict() with iterating keys
                    edges = self.nxGraph[ID1][ID2]
                    for edge in edges:
                        if (type(edges[edge]['conns'][0]) == type(connections[0])):
                            
                            existingConnections = edges[edge]['conns']

                            # check that duplicate edges are not added
                            for c in connections:
                                hasConnection = False
                                for c2 in existingConnections:
                                    if (c.name == c2.name):
                                        hasConnection = True
                                if not hasConnection:
                                    # add connections to the list
                                    existingConnections.append(c)
                                    edges[edge]['title'] += "\n" + c.name
                                    edges[edge]['weight'] = min(20, len(existingConnections))

                            notAdded = False

                # if no edge of same connection type is in the graph between ID1 and ID2, add the edge
                if (notAdded):
                    # get title of the edge
                    titleStr = ""
                    first_seen = None
                    last_seen = None
                    for con in connections:
                        titleStr += " Works: \n" + con.name

                        for con in connections:
                            if last_seen is None and con.date:
                                last_seen = con.date
                            elif last_seen and con.date:
                                last_seen = con.date if compare_dates(
                                    last_seen, con.date) else last_seen
                            if first_seen is None and con.date:
                                first_seen = con.date
                            elif first_seen and con.date:
                                first_seen = con.date if not compare_dates(
                                    first_seen, con.date) else first_seen

                    self.nxGraph.add_edge(ID1, ID2, title=titleStr,
                                          first_seen=first_seen, last_seen=last_seen,
                                           conns=connections, weight=min(20, len(connections)), color=connections[0].getColor())

    def search(self, authorID: str):
        """Returns the node that the author is in or None if the
        author is not in the graph."""
        if (authorID in self.lookupAuthor):
            return self.lookupAuthor[authorID]
        else:
          return None

    def getDisplayInfo(self):
        nt = Network(height="500px", width="500px", filter_menu=True)
        nt.from_nx(self.nxGraph)

        ids = nt.get_nodes()
        nodes = []
        for id in ids:
            nodes.append(nt.get_node(id))

        edges = nt.get_edges()
        return [nodes, edges]

    def make_js(self):
        nt = Network(height="500px", width="500px", filter_menu=True)
        nt.from_nx(self.nxGraph)

        ids = nt.get_nodes()
        nodes = []
        for id in ids:
            nodes.append(nt.get_node(id))

        edges = nt.get_edges()

        with open("nodesAndEdges.js", "w") as outfile:
                outfile.write('var nodesList = ')
                json.dump(nodes, outfile)
                outfile.write(';\n')
                outfile.write('var edgesList = ')
                json.dump(edges, outfile)
                outfile.write(';')

    def make_html(self):
        nt = Network(height="500px", width="500px", filter_menu=True)
        nt.from_nx(self.nxGraph)
        nt.barnes_hut(gravity=-1000, central_gravity=0.3, spring_length=250,
                      spring_strength=0.001, damping=0.09, overlap=.5)
        nt.show("nx.html")


known_authors_dict = {}
known_inventors_dict = {}


def expand_graph(graph: Graph, researcherIds: list[tuple]):
    """Creates or expands the graph based on a researcherID and startingNode. The researcherId
        should be in the starting node. If empty graph is passed in, graph and startingNodeID
        will be None.
        """
    # if node is not created yet, create it with root node
    if graph == None:
        graph = Graph()
        
        # Add each researchId tuple (in case there are multiple roots)
        for i in range(len(researcherIds)):
            if researcherIds[i][0] != lookup_classes[0].skipid:
                name = lookup_classes[0].get_name(str(researcherIds[i][0]))
            else:
                name = lookup_classes[1].get_name(str(researcherIds[i][1]))
            # Create root, add node, save it as the root
            root = Author(researcherIds[i], name, [])
            graph.addNode([root])

            startingNodeID = graph.search(researcherIds[i])
            graph.roots.append(startingNodeID)
            graph.depths.append(0) # Current depth from that node is 0

            # set expanded node to expanded
            graph.nxGraph.nodes[startingNodeID]["expanded"] = True

            if researcherIds[i][0] != lookup_classes[0].skipid and researcherIds[i][1] != lookup_classes[1].skipid:
                    graph.lookupAuthor[(int(researcherIds[i][0]), int(researcherIds[i][1]))] = startingNodeID
            elif researcherIds[i][1] != lookup_classes[1].skipid:
                    graph.lookupAuthor[(researcherIds[i][0], int(researcherIds[i][1]))] = startingNodeID
            else:
                    graph.lookupAuthor[(int(researcherIds[i][0]), researcherIds[i][1])] = startingNodeID
            
    for i in range(len(researcherIds)):
        # add new nodes and edges for research papers
        if researcherIds[i][0] != lookup_classes[0].skipid:
            lookup = lookup_classes[0]
            if int(researcherIds[i][0]) > 0:     
                papers = lookup.get_connections(str(researcherIds[i][0]))

                # Get all coauthors
                for paper in papers:
                    for author in paper["authors"]:
                        if author["authorId"] == None:
                            continue

                        known_authors_dict[author["authorId"]] = Author((int(author["authorId"]), 0), author["name"], [])
                        
                # For every author, find out if they have a corresponding PatentsView Id
                bulk_lookup(known_authors_dict, known_inventors_dict)
                
                for paper in papers:
                    authors = paper["authors"]
                    authorObjectList = set()

                    if len(authors) == 1 and authors[0] == researcherIds[i][0]:
                        continue
                    for author in authors:
                        if author["authorId"] == None or author["authorId"] == researcherIds[i][0]:
                            continue
                        else:
                        # still need to add the works in the author objetcs. Don't really
                        # know how to do this yet.
                            if author["authorId"] in known_authors_dict:
                                newAuthor = known_authors_dict[author["authorId"]]
                            else:
                                newAuthor = Author((int(author["authorId"]), 0), author["name"], [])

                                known_authors_dict[author["authorId"]] = newAuthor
                            authorObjectList.add(newAuthor)

                    if len(authorObjectList) == 0:
                        continue

                    newNodesID = graph.addNode(list(authorObjectList))
                    startingNodeID = graph.search(researcherIds[i])

                    # set expanded node to expanded
                    graph.nxGraph.nodes[startingNodeID]["expanded"] = True

                    for nodeID in newNodesID:
                        newPublication = Publication(paper["title"], paper["publicationDate"], authors, "")
                        graph.addEdge(startingNodeID, nodeID, [newPublication])

        # add new nodes and edges for patents
        if researcherIds[i][1] != lookup_classes[1].skipid:
            lookup = lookup_classes[1]
            if int(researcherIds[i][1]) > 0:
                patents = lookup.get_connections(str(researcherIds[i][1]))
                
                # Get all coauthors
                for patent in patents["patents"]:
                    for inventor in patent["inventors"]:
                        known_inventors_dict[inventor["inventor_key_id"]] = Author((0, int(inventor["inventor_key_id"])), inventor["inventor_first_name"] + " " + inventor["inventor_last_name"], [])

                # For every author, find out if they have a corresponding PatentsView Id
                bulk_lookup(known_authors_dict, known_inventors_dict)

                for patent in patents["patents"]:
                    inventors = patent["inventors"]
                    inventorObjectList = set()
                    if len(inventors) == 1 and inventors[0]["inventor_key_id"] == researcherIds[i][1]:
                        continue
                    for inventor in inventors:
                        inventor = inventor["inventor_key_id"]

                        if inventor == None or inventor == researcherIds[i][1]:
                            continue
                        else:
                        # still need to add the works in the author objetcs. Don't really
                        # know how to do this yet.
                            if inventor in known_inventors_dict:
                                newInventor = known_inventors_dict[inventor]
                            else:
                                name = lookup.get_name(inventor)
                                newInventor = Author((0, inventor), name, [])
                            inventorObjectList.add(newInventor)

                    newNodesID = graph.addNode(list(inventorObjectList))
                    startingNodeID = graph.search(researcherIds[i])
                    for nodeID in newNodesID:

                        newPublication = Patent(patent["patent_title"], patent["patent_date"], inventors, "")
                        graph.addEdge(startingNodeID, nodeID, [newPublication])
        
    graph.recolor_nodes()
    graph.recolor_edges()
    
    return graph
