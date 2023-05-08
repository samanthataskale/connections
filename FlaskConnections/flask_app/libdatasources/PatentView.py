import requests
import json
import urllib
from libdatasources.DataSource import DataSource

def format_patent_ids(arr):
    str = "["
    for patent in arr:
        str += f'"{patent}",'
    str = str[0:-1]
    str += "]"
    print(str)
    return str

class PatentView(DataSource):
    source = "Patents View"
    aliases = False
    skipid = "skipPV"

    #legacy lookup strings
    """
    inventor_base = "https://search.patentsview.org/api/v1/inventor/"
    patent_base = "https://search.patentsview.org/api/v1/patent/"
    inventor_id_get = '["inventor_id", "inventor_first_seen_date", "inventor_last_seen_date", "inventor_num_patents", "inventor_lastknown_city"]'
    inventor_name_get = '["inventor_name_first", ""inventor_name_last"]'
    """

    inventor_base = "https://api.patentsview.org/inventors/query"
    patent_base= "https://api.patentsview.org/api/v1/patent/"
    f_url = 'f='
    inventor_id_get = '["inventor_key_id","inventor_first_seen_date","inventor_last_seen_date","inventor_total_num_patents","inventor_lastknown_city","inventor_first_name","inventor_last_name"]'
    inventor_disambig_get = '["inventor_first_name","inventor_last_name","inventor_first_seen_date","inventor_last_seen_date"]'
    inventor_name = '["inventor_first_name","inventor_last_name"]'
    paper_graph_get = '["patent_id", "patent_number", "patent_title", "patent_date","inventor_id","inventor_location_id","inventor_city","inventor_state","inventor_country","inventor_first_name","inventor_last_name"]'
    q_url = 'q='

    headers = {
    'Accept': 'application/json',
    'X-Api-Key' : "PTnUaBAQ.z8XnfmwGcWQ6eCiNIZIOec3oW5C66uPL"
    }


   
    @classmethod
    def do_patentview_query(cls, base, f_string, q_string):
        f_part = cls.f_url + f_string
        q_part = cls.q_url + q_string
        url = base + "?" + q_part + "&" + f_part #q and f reversed for legacy
        raw_response = requests.get(url, headers = cls.headers)

        if raw_response.status_code != 200:
            
            print(f"Bad response! Got code {raw_response.status_code}. Response: {raw_response.content}")
            return None

        response = json.loads(raw_response.content)
        return response
    @classmethod
    def split_name(cls, name):
        names = name.split()
        if len(names) > 2: #remove any middle names
            names = [ names[0], names[-1]  ]
        if len(names) == 2:
            fn_dict = {"inventor_first_name":names[0]} #search: name_first
            ln_dict = {"inventor_last_name":names[1]} #search: name_last
            query_body_json = json.dumps( {"_and":[fn_dict, ln_dict]} )
        elif len(names) == 1:
            ln_dict = {"inventor_last_name":names[0]}
            query_body_json = json.dumps( ln_dict )
        return query_body_json

    @classmethod
    def get_name_from_id(cls, inventor_id):
        id_dict = {"inventor_key_id":inventor_id}
        query_body_json = json.dumps( id_dict )

        f_string = urllib.parse.quote_plus(cls.inventor_disambig_get)
        q_string = urllib.parse.quote_plus(query_body_json)

        response = cls.do_patentview_query(cls.inventor_base, f_string, q_string)
        if response == [] or response["count"] == 0:
            return None
        first_name = response["inventors"][0]["inventor_first_name"]
        last_name = response["inventors"][0]["inventor_last_name"]

        first_seen = response["inventors"][0]["inventor_first_seen_date"]
        last_seen = response["inventors"][0]["inventor_last_seen_date"]
        return {"name":first_name + " " + last_name, "sourceId": inventor_id, \
                         "first_seen": first_seen, "last_seen":last_seen}

    @classmethod
    def check_id(cls, inventor_id):
        id_dict = {"inventor_key_id":inventor_id}
        query_body_json = json.dumps( id_dict )

        f_string = urllib.parse.quote_plus(cls.inventor_disambig_get)
        q_string = urllib.parse.quote_plus(query_body_json)

        response = cls.do_patentview_query(cls.inventor_base, f_string, q_string)
        return (response is not None)

    @classmethod
    def remove_duplicate_names(cls, names):
        unique_names = []
        for name in names:
            split_names = name.split()
            if len(split_names) > 1: #remove any middle names
                comb_name = " ".join([ split_names[0], split_names[-1]  ])
            elif len(split_names) == 1:
                comb_name = split_names[0]
            unique_names.append(comb_name)
        return (list(set(unique_names)))

    @classmethod 
    def check_name(cls, name):
        query_body_json = cls.split_name(name)

        f_string = urllib.parse.quote_plus(cls.inventor_id_get)
        q_string = urllib.parse.quote_plus(query_body_json)

        response = cls.do_patentview_query(cls.inventor_base, f_string, q_string)
        if response is None or response["count"] == 0:
            False
        return True

    @classmethod
    def get_disamb_from_name(cls, names: list[str]) -> list:
        if len(names) == 0:
            return []
        
        patent_body = []
        names = cls.remove_duplicate_names(names)
        query_body_json = '{"_or" : ['
        for name in names:
            query_body_json += cls.split_name(name)
            if names[-1] != name:
                query_body_json += ","
        
        query_body_json += ']}'
        
        # Max URL length is 2048 characters, so break up the query into two if needed
        if len(query_body_json) > 1800:
            first_half = cls.get_disamb_from_name(names[0:int(len(names)/2)])
            second_half = cls.get_disamb_from_name(names[int(len(names)/2):-1])
            return first_half + second_half
        
        f_string = urllib.parse.quote_plus(cls.inventor_id_get)
        q_string = urllib.parse.quote_plus(query_body_json)

        response = cls.do_patentview_query(cls.inventor_base, f_string, q_string)
        
        if response is None or response["count"] == 0:
            return []
        
        for inventor in response["inventors"]:
            inventor_dict = {   "sourceId":inventor["inventor_key_id"], "name":name, 
                                "first_seen":inventor["inventor_first_seen_date"],
                                "last_seen":inventor["inventor_last_seen_date"], "last_city":inventor["inventor_lastknown_city"],
                                "numPatents":inventor["inventor_total_num_patents"] }
            patent_body.append(inventor_dict)
        patent_body = DataSource.remove_duplicate(patent_body)
        patent_body = sorted(patent_body, key=lambda d: d['numPatents'], reverse=True)
        return patent_body

    """These are used for graph creation"""
    @classmethod
    def get_name(cls, id: str):
        id_dict = {"inventor_key_id":id}
        query_body_json = json.dumps( id_dict )

        f_string = urllib.parse.quote_plus(cls.inventor_name)
        q_string = urllib.parse.quote_plus(query_body_json)

        response = cls.do_patentview_query(cls.inventor_base, f_string, q_string)
        if response == [] or response == None or response["count"] == 0:
            return None
        first_name = response["inventors"][0]["inventor_first_name"]
        last_name = response["inventors"][0]["inventor_last_name"]
        return first_name + " " + last_name

    @classmethod
    def get_connections(cls, ID):
        """
        Returns a list of dictionaries which contain the following attributes
        {patent_id, patent_number, patent_title}
        """
        inv = "https://api.patentsview.org/patents/query?q={\"inventor_key_id\":\"%s\"}" %ID
        inv += "&" + cls.f_url + cls.paper_graph_get

        url = urllib.parse.quote(inv)
        r = requests.get(url = inv, headers = PatentView.headers)
        response = json.loads(r.content)
        return response
    
    @classmethod
    def get_connection_sourceIDs(cls, ID):

        inv = "https://api.patentsview.org/patents/query?q={\"patent_id\":\"%s\"}&f=[\"inventor_key_id\"]" %ID
        url = urllib.parse.quote(inv)
        r = requests.get(url = inv, headers = PatentView.headers)
        response = json.loads(r.content)
 
        invs = response['patents'][0]['inventors']
        co_auths = []
 
        for inv in invs:
            co_auths.append(inv['inventor_key_id'])

        return co_auths


"""
if response["count"] == 0:
    print("no records found")
    exit()

    person_url = "https://api.patentsview.org/patents/query?q="
    inventor_key = f'{{%22inventor_key_id%22:%22{inventor["inventor_key_id"]}%22}}'
    
    raw_response = requests.get(person_url + inventor_key )

    if raw_response.status_code != 200:
        print(f"Bad response! Got code {raw_response.status_code}. Exiting :(")

        exit()
    response = json.loads(raw_response.content)
    #print(response)

    patent_ids = [ patent["patent_id"] for patent in response["patents"] ]
    ids_url = f'{{%22patent_id%22:{format_patent_ids(patent_ids)}}}'
    more_info = '&f=["inventor_key_id","patent_date"]'
    #print(person_url + ids_url + more_info)
    raw_response = requests.get(person_url + ids_url + more_info)
    if raw_response.status_code != 200:
        print(f"Bad response! Got code {raw_response.status_code}. Exiting :(")

        exit()

    response = json.loads(raw_response.content)
    # get_date_ranges(  [patent["patent-date"].split("-") for patent in response["patents"] )

    print(response)
"""
