from googlesearch import search

def web_search(query):
    """Perform a Google search and print the top 5 results.

    Args:
        query (str): The search query string.
    """
    results = search(query, num_results=5)
    for result in results:
        print(result)