from abc import abstractmethod
import requests
import json

class SearchClient():
    """
    Search Engine Client Base Class
    """
    def __init__(self, endpoint, max_results, min_index, headers=None, params=None):
        self.headers = headers
        self.params = params
        self.endpoint = endpoint
        self.max_results_per_q = max_results
        self.min_index = min_index
        self.response = None

    @abstractmethod
    def _check_value(self, **kwargs):
        """
        Verify value of keyworded arguments to be passed to the request's parameters.
        """
        pass

    @abstractmethod
    def _parse_response(self):
        """
        Extract items (and their specified parameters) from the request's response and return them
        in the form of a list of items (each item being a dict).
        """
        pass

    def search(self, query, **kwargs):
        """
        Execute search request to the specified endpoint from a defined query and parameters.
        Returns response in a list of dictionaries (one dict per item) generated by the 
        _parse_response method.
        """
        if not query:
            raise ValueError("Expected a query")
        self._check_value(**kwargs)

        self.params.update(q=query, **kwargs)
        self.response = requests.get(self.endpoint, headers=self.headers, params=self.params).json()
        return self._parse_response()

class GoogleCustomSearchClient(SearchClient):
    """
    Google Custom Search Engine Client
    """
    def __init__(self, cse_id, api_key):
        if not api_key:
            raise ValueError("Expected an API Key")
        if not cse_id:
            raise ValueError("Expected a Custom Search Engine ID")
        super().__init__("https://www.googleapis.com/customsearch/v1", 10, 1,
                         {}, {'key':api_key, 'cx':cse_id, 'searchType':'image'})

    def _check_value(self, **kwargs):
        start = kwargs.pop('start', 1)
        num = kwargs.pop('num', None)
        if kwargs:
            raise TypeError("%r are invalid keyword arguments." % (kwargs.keys()))
        if num is None:
            raise ValueError("Missing number of results to return.")
        if start < self.min_index:
            raise ValueError("Invalid start index value. Valid values start at {}.".format(
                self.min_index))
        if num > self.max_results_per_q or num < self.min_index:
            raise ValueError(("Invalid num value. Number of search results to return must"
                              " be between {} and {}, inclusive.".format(
                                  self.min_index, self.max_results_per_q)))

    def _parse_response(self):
        items = []
        for item in self.response['items']:
            items.append({
                'type': item['mime'],
                'width': item['image']['width'],
                'height': item['image']['height'],
                'size': item['image']['byteSize'],
                'url': item['link'],
                'hostPage': item['image']['contextLink']
            })
        return items

class BingSearchClient(SearchClient):
    """
    Bing Image Search Client
    """
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Expected an API Key")
        super().__init__("https://api.cognitive.microsoft.com/bing/v7.0/images/search", 150, 1,
                         {'Ocp-Apim-Subscription-Key':api_key}, {})

    def _check_value(self, **kwargs):
        offset = kwargs.pop('offset', 0)
        count = kwargs.pop('count', None)
        if kwargs:
            raise TypeError("%r are invalid keyword arguments." % (kwargs.keys()))
        if count is None:
            raise ValueError("Missing number of results to return.")
        if offset < self.min_index - 1:
            raise ValueError("Invalid offset index value. Valid values start at {}.".format(
                self.min_index - 1))
        if count > self.max_results_per_q or count < self.min_index:
            raise ValueError(("Invalid count value. Number of search results to return must"
                              " be between {} and {}, inclusive.".format(
                                  self.min_index, self.max_results_per_q)))

    def _parse_response(self):
        items = []
        for item in self.response['value']:
            items.append({
                'type': item['encodingFormat'],
                'width': item['width'],
                'height': item['height'],
                'size': item['contentSize'],
                'url': item['contentUrl'],
                'hostPage': item['hostPageDisplayUrl']
            })
        return (items, self.response['nextOffset'], self.response['totalEstimatedMatches'])