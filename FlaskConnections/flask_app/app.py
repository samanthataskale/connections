#!/usr/bin/env python
"""
Created on
@author: Yair, Theresa
This code was created for CMSC435 Team 01's Connections Project Spring 2023
This is the main Flask file that controls what happens with each of the website's endpoints
"""
from flask_wtf.csrf import CSRFProtect
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import urllib
import logging
import ast
from werkzeug.middleware.profiler import ProfilerMiddleware

app = Flask(__name__)

# Profile the app (aka see how long it spent in different functions)
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app, sort_by=["cumulative"], restrictions=["connect2", 20])

app.config['SECRET_KEY'] = 'my-secret-key'
csrf = CSRFProtect(app)

import json
from lookup_forms import NameSearchForm, IDSearchForm, lookup_classes
from GraphClass.GraphClass import Graph, expand_graph
import pickle

import os

#the main welcome page
@app.route('/', methods=['POST', 'GET'])
def index():
    """Handles the main page with the user lookup"""
    #two different types of inputs
    f = NameSearchForm()
    g = IDSearchForm()

    #figure out which form was submitted based on the submit name
    which_form_submitted = None
    for entry in request.form:
        which_form_submitted = f if str(entry) == "submitname" else None
        if which_form_submitted:
            break
        which_form_submitted = g if entry == "submitid" else None
        if which_form_submitted:
            break

    #set default values
    name = ""
    id_array = [None] * len(lookup_classes)
    if which_form_submitted == f and f.validate_on_submit():
        #grab the names of the people
        person1 = {"name" : f.search_query.data, "ids" : str(id_array)}
        person2 = {"name" : f.search_query_two.data, "ids" : str(id_array)}
        people = [person1, person2]
        return redirect(url_for('author_disambig', people = people ))
    elif which_form_submitted == g and g.validate_on_submit():
        #grab the input ids
        name = urllib.parse.quote_plus(name)
        id_array = [g.iddata.data if g.idsource.data == x.source else None for x in lookup_classes]
        id_array_two = [g.iddata_two.data if g.idsource_two.data == x.source else None for x in lookup_classes]
        person1 = {"name" : name, "ids" : str(id_array)}
        person2 = {"name" : name, "ids" : str(id_array_two)}
        people = [person1, person2]
        #id_array = urllib.parse.quote(str(id_array))
        return redirect(url_for('author_disambig', people = people))

    return render_template('index.html', form = f, form2 = g)

@app.route('/author-disambig/', methods=['GET'])
def author_disambig():
    """Handles the author disambiguation stages"""
    sent_in = request.args.to_dict(flat=False)
    people = []

    #get the list of people to verify - length of people should be the number of people the user intended
    try:
        for person in sent_in["people"]:
            parsed = ast.literal_eval(person)
            IDs = ast.literal_eval(parsed["ids"])
            IDs = [x if x != "" else None for x in IDs]
            print(parsed)
            if len(parsed["name"]) > 0:
                people.append(  {"name":parsed["name"], "IDs": IDs})
            else:
                if not all(x == None for x in IDs):
                    people.append(  {"name":"", "IDs": IDs})
    except e:
        print(e)
        return show_error(f"Invalid URL")

    #results is a 2d array. the main elements are per person, which the entries being for each source
    results = []
    known_id = [-1] * len(people) #holds the index of the knownid, -1 if not
    try:
        for j, person in enumerate(people):
            name = person["name"]
            IDs = person["IDs"]
            #print(name, IDs)
            results.append([])
            results[j] = [[]] * len(lookup_classes)

            if len(name) > 1: #if there is a name, that is
                for i, lookup in enumerate(lookup_classes):
                    results[j][i] = lookup.get_disamb_from_name([name])
                    if len(results[j][i]) > 0 and lookup.aliases:
                        #as soon as you get to a class with aliases, you don't need to do any more lookups
                        #as it will be redone anyway
                        break
            elif IDs != ([None] * len(lookup_classes)):
                #Get lookup name
                known_class_has_alias = False
                for i, lookup_class in enumerate(lookup_classes):
                    #see if an id was even passed in for this source
                    worth_testing = (IDs[i] is not None) and (len(IDs[i]) > 0)
                    if worth_testing and lookup_class.check_id(IDs[i]):
                        author_info = lookup_class.get_name_from_id(IDs[i])
                        if author_info is None:
                            break
                        name = author_info["name"]
                        results[j][i] = [author_info]
                        known_id[j] = i
                        known_class_has_alias = lookup_class.aliases
                        break
                    elif worth_testing:
                        return show_error(f"Invalid Id for {lookup_class.source}")
                if name == "NONAME" or name == "":
                    return show_error(f"Invalid Ids")
                person["name"] = name

                if known_class_has_alias:
                    continue

                #do other lookups
                for i, lookup_class in enumerate(lookup_classes):
                    if known_id[j] != i:
                        results[j][i] = lookup_class.get_disamb_from_name(name)

    except Exception as e:
        logging.exception("Failed to get author ids or something")
        return show_error(f"Some lookup went wrong")

    #combine all of the results
    #another 2d array, similar to results, but with added information
    sources = []
    for j in range(len(people) ):
        this_person_info = []
        for i, lookup_class in enumerate(lookup_classes):
            this_person_info.append({"results" : results[j][i],
                        "defin": known_id[j] == i,
                        "hasaliases": lookup_class.aliases,
                        "skipid" : lookup_class.skipid})
        sources.append(this_person_info)

    return render_template('query_results.html',
                            names = [x["name"] for x in people],
                            sources = sources)

@app.route('/graph')
def make_graph():
    names = request.args.get("names").split(",")
    all_IDs = request.args.get("ids").split(",")

    indexes = []
    index = 0
    while index <  len(names):
        if (names[index]  == ""):
            indexes.append(index)
        index = index + 1

    for i in indexes:

        names.pop(i)
        all_IDs.pop(2*i)
        all_IDs.pop(2*i)


    print(names, all_IDs)
    # If we've imported the graph, you can skip all this initialization
    if all_IDs[0] != "import":
        for j in range(len(names)):
            IDs = all_IDs[j * len(lookup_classes): (j+1)* len(lookup_classes)]
            print(IDs)
            if all(x == lookup_classes[i].skipid for i, x in enumerate(IDs)) :
                return show_error(f"You need to specify at least one ID.")

            #verify the ids again
            if len(IDs) > len(lookup_classes):
                return show_error(f"Too many IDS in the URL: got {len(IDs)}, expected {len(lookup_classes)}")
            elif len(IDs) < len(lookup_classes):
                return show_error(f"Too few IDS in the URL: got {len(IDs)}, expected {len(lookup_classes)}")
            for i, lookup_class in enumerate(lookup_classes):
                if not IDs[i] == lookup_class.skipid and not lookup_class.check_id( IDs[i] ):
                    return show_error(f"Invalid Id for {lookup_class.source}")

    return render_template('graph.html', names = names, ids = all_IDs)
    #except Exception as e:
    #    print(e)
    #    return redirect(url_for('index'))

@app.route('/getmoreentries', methods=['POST'])
def get_more_entries():
    index = request.get_json(force=True)["index"]
    aliases = request.get_json(force=True)["aliases"]
    results = lookup_classes[index].get_disamb_from_name(aliases)

    #print("results from mid disamb fetching", results)
    return jsonify( results )

@app.route('/expandgraph', methods=['POST'])
def expand():
    req = request.get_json(force=True)
    nodes = req['ids'] # This should be a list of tuples
    ident = req['identifier']
    #print(ids)
    newList = []
    f_name = './data/graphObj_' + str(ident) + '.pkl'
    with (open(f_name, "rb")) as openfile:
        newList.append(pickle.load(openfile))

    newGraph = newList[0]
    ids = [tuple(author["IDs"]) for node in nodes for author in node["auths"]]
    
    newGraph = expand_graph(newGraph, ids)
    
    with open(f_name, 'wb') as file:
        pickle.dump(newGraph, file)

    return jsonify( newGraph.getDisplayInfo() )

@app.route('/deletenode', methods=['POST'])
def delete():
    req = request.get_json(force=True)

    # id = req['ids'][0]['auths'][0]['IDs']
    nodes = req['ids']
    ids = [tuple(author["IDs"]) for node in nodes for author in node["auths"]]
    ident = req['identifier']

    newList = []
    f_name = './data/graphObj_' + str(ident) + '.pkl'
    with (open(f_name, "rb")) as openfile:
        newList.append(pickle.load(openfile))

    newGraph = newList[0]
    newGraph.deleteNode(ids[0])

    with open(f_name, 'wb') as file:
        pickle.dump(newGraph, file)

    return jsonify( newGraph.getDisplayInfo() )

@app.route('/buildgraph', methods=['POST'])
def build_graph():
    params = request.get_json(force=True)
    #the dataids should just be a flat list that needs to be turned into a 2d thing ~ theresa
    ids = params['data']['dataids'] # This should be a list of all the researcher tuples
    num_names = params['data']['numNames']
    print(ids)
    if (ids[0] != "import"):
        if (num_names * len(lookup_classes) != len(ids)):
            message = "Invalid number of ids for the number of initial names"
            return render_template('error_page.html', error_message = message)
        skip = len(lookup_classes)
        ids = [ tuple( ids[j: j + skip]  ) for j in range(0, len(ids), skip)  ]
        print(ids)
    """
    if type(ids[0]) is list:
        # This is the future - the API should be called with parames['data']['dataids'] being a list of researcher tuples
        ids = [tuple(id) for id in ids] # Convert to a list of tuples
    else:
        # This will be triggered if we only send 1 researcher tuple and not in a list form
        # TODO: Get rid of this when it is no longer needed and we're always just sending lists of researcher tuples
        ids = [tuple(ids), ('2056512963','68484')]"""

    print(f"ids are {ids}")
    identifier = str(params['data']['identifier'])

    # Check if we are importing a file
    if ids[0] == "import" and len(ids) >= 2:
        f_name = './data/graphObj_' + str(ids[1]) + '.pkl'
        
        if os.path.isfile(f_name):
            # We're going to have to switch the file name to the new version
            with (open(f_name, "rb")) as openfile:
                graph = pickle.load(openfile)

    # Just your standard build a new graph scenario
    else:
        graph = expand_graph(None, ids)

    with open("./data/graphObj_" + identifier + ".pkl", 'wb') as file:
        pickle.dump(graph, file)

    return jsonify( graph.getDisplayInfo() )

@app.route('/info')
def infopage():
    return render_template('information.html')

@app.route('/deletepkl', methods=['POST'])
def delete_pkl():
    identi = request.get_json(force=True)['rand']
    filename = "./data/graphObj_" + str(identi) + ".pkl"
    if os.path.exists(filename):
        os.remove(filename)
    return jsonify(42)

@app.route('/exportjson', methods=['POST'])
def export_graph_as_json():
    req = request.get_json(force=True)
    ident = req['identifier']

    f_name = './data/graphObj_' + str(ident) + '.pkl'
    with (open(f_name, "rb")) as openfile:
        graph_obj: Graph = pickle.load(openfile)
        return graph_obj.to_json()

@app.route('/importjson', methods=['POST'])
def import_graph_as_json():
    req = request.get_json(force=True)
    graph = req['graph']
    identifier = req['identifier']

    # Create the graph and pickle it!
    # Not really necessary to reserialize the graph variable but I do it anyway because it makes the Graph.from_json more parallel to to_json
    graph = Graph.from_json(json.dumps(graph))
    with open("./data/graphObj_" + str(identifier) + ".pkl", 'wb') as file:
        pickle.dump(graph, file)

    return render_template('graph.html', names = 'import', ids = "")

def show_error(message):
    print(message)
    return render_template('error_page.html', error_message = message)
