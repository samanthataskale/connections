import requests
import json
import urllib
from wtforms.validators import ValidationError
from libdatasources.DataSource import DataSource
import concurrent.futures

def compare_dates(date1, date2):
    return date2 > date1

class SemanticScholar(DataSource):
    source = "Semantic Scholar"
    aliases = True
    skipid = "skipSS"


    base_url = 'https://api.semanticscholar.org/graph/v1/'
    disambig_fields = "fields=aliases,name,hIndex,url,paperCount,papers.title,papers.citationCount,papers.publicationDate"

    headers = {'Authorization':"l9uaXpjOFe47eNmnNyFTG3JGeHzMkswSaGqNlDjq"}

    def __init__(self):
        self.sess = requests.Session()
        #self.sess.headers.update({'User Agent': 'CMSC388J Spring 2021 Project 2'})

    """These are used for author disambiguation"""
    @classmethod
    def get_disamb_from_name(cls, names: list[str]) -> list[dict]:
        """
        Searches the API for the supplied search_string, and returns
        a list of Researcher objects if the search was successful, or the error response
        if the search failed.

        Only use this method if the user is using the search bar on the website.
        """

        if len(names) == 0:
            return []

        authors = []

        if len(names) < 5:
            for name in names:
                authors += cls.helper_get_disamb_from_name(name)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(names)) as executor:
                future_to_name = {executor.submit(cls.helper_get_disamb_from_name, name): name for name in names}
                for future in concurrent.futures.as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        print('%r generated an exception: %s' % (name, exc))
                    else:
                        authors += result

        authors = DataSource.remove_duplicate(authors)
        authors = sorted(authors, key=lambda d: d['hIndex'], reverse=True)
        return authors

    @classmethod
    def helper_get_disamb_from_name(cls, name: str) -> list[dict]:
        authors = []
        search_url = f'author/search?query={urllib.parse.quote_plus(name)}'

        url = cls.base_url + search_url + "&" + cls.disambig_fields
        raw_response = requests.get(url, headers = cls.headers)
        if raw_response.status_code != 200:
            return []
        response = json.loads(raw_response.content)

        if response['total'] == 0:
            return []

        # #get the ids of those authors
        # author_ids = [author["authorId"] for author in response["data"] ]

        # #do a batch search for the ids obtained
        # batch_url = "author/batch?" + cls.disambig_fields
        # json_data = {"ids":author_ids}
        # raw_response = requests.post(cls.base_url + batch_url, json = json_data)
        # if raw_response.status_code != 200:
        #     return -1
        # response = json.loads(raw_response.content)

        for author in response["data"]:
            most_cited_paper = ""
            most_citations = 0


            first_seen = None
            last_seen = None

            for paper in author["papers"]:
                most_cited_paper = paper["title"] if paper["citationCount"] > most_citations else most_cited_paper
                most_citations = paper["citationCount"] if paper["citationCount"] > most_citations else most_citations
                if first_seen is None:
                    first_seen = paper["publicationDate"]
                    last_seen = paper["publicationDate"]
                elif paper["publicationDate"] is not None:
                    last_seen = paper["publicationDate"] if compare_dates( last_seen, paper["publicationDate"] ) else last_seen
                    first_seen = paper["publicationDate"] if not compare_dates( first_seen, paper["publicationDate"] ) else first_seen
            author_dict = {  "sourceId": author["authorId"] ,"name": author["name"], "hIndex":author["hIndex"], \
                        "paperCount": author["paperCount"], "paper": most_cited_paper, \
                        "first_seen": first_seen, "last_seen": last_seen, \
                        "aliases": author["aliases"], "url": author["url"]}

            authors.append(author_dict)

        return authors

    @classmethod
    def check_id(cls, sourceid):
        id_url = f"author/{urllib.parse.quote_plus(sourceid)}"
        raw_response = requests.get(cls.base_url + id_url)
        if raw_response.status_code != 200:
            #print(f"Bad response! Got code {raw_response.status_code}. Exiting :(")
            return False
        return True
    @classmethod
    def check_name(cls, name):
        search_url = f'author/search?query={urllib.parse.quote_plus(name)}"'

        #print(f"Fetching url {self.base_url + search_url}")
        raw_response = requests.get(cls.base_url + search_url, headers = cls.headers)
        if raw_response.status_code != 200:
            #print(f"Bad response! Got code {raw_response.status_code}. Exiting :(")
            return False
        response = json.loads(raw_response.content)

        if response['total'] == 0:
            return False
        return True
    @classmethod
    def get_name_from_id(cls, sourceid):
        id_url = f"author/{urllib.parse.quote_plus(sourceid)}?" + cls.disambig_fields
        raw_response = requests.get(cls.base_url + id_url)

        if raw_response.status_code != 200:
            print(f"Bad response! Got code {raw_response.status_code}. Response: {raw_response.content}")
            return None
        response = json.loads(raw_response.content)
        first_seen = None
        last_seen = None

        for paper in response["papers"]:
            if first_seen is None:
                first_seen = paper["publicationDate"]
                last_seen = paper["publicationDate"]
            elif paper["publicationDate"] is not None:
                last_seen = paper["publicationDate"] if compare_dates( last_seen, paper["publicationDate"] ) else last_seen
                first_seen = paper["publicationDate"] if not compare_dates( first_seen, paper["publicationDate"] ) else first_seen

        return {  "sourceId": response["authorId"], "name": response["name"], \
                        "paperCount": response["paperCount"], \
                        "first_seen": first_seen, "last_seen": last_seen, \
                        "aliases": response["aliases"] }

    """These are used for graph creation"""
    @classmethod
    def get_name(cls, id: str):
        url = cls.base_url + f"author/{urllib.parse.quote_plus(id)}?fields=name"
        raw_response = requests.get(url)
        response = json.loads(raw_response.content)

        if raw_response.status_code != 200:
            print(f"Bad response! Got code {raw_response.status_code}. Response: {raw_response.content}")
            exit()
        return response["name"]
    @classmethod
    def get_connection_sourceIDs(cls, id: str):
        """Gets authors of a research paper from semantic scholar."""
        url = cls.base_url + f"paper/{urllib.parse.quote_plus(id)}?fields=authors"
        raw_response = requests.get(url)
        response = json.loads(raw_response.content)

        if raw_response.status_code != 200:
            print(f"Bad response! Got code {raw_response.status_code}. Exiting :(")
            exit()

        authorList = []
        for person in response["authors"]:
            authorList.append(person["authorId"])

        return authorList
    @classmethod
    def get_connections(cls, id: str):
        """Get research papers by an author from Semantic Scholar."""
        url =  cls.base_url + f"author/{urllib.parse.quote_plus(id)}?fields=papers.paperId,papers.title,papers.publicationDate,papers.authors"
        response = json.loads(requests.get(url).content)
        return response["papers"]


