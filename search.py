from ddgs import DuckDuckSearch

# Initialize the searcher with your desired configuration.
searcher = DuckDuckSearch(
    top_k=10,
    max_results=20,
    region="wt-wt",
    safesearch="moderate",
    allowed_domain="",  # Leave empty for no domain restriction
    use_answers=False   # Set to True if you want to retrieve direct answers from DuckDuckGo
)

# Define your search query and number of results to retrieve.
query = "What is Python?"
num_results = 5

# Perform the search.
results = searcher.search(query, num_results)

# Output the results.
print("Documents:")
for doc in results["documents"]:
    print(f"Title: {doc.title}")
    print(f"Content: {doc.content}")
    print(f"Link: {doc.link}")
    print("------------")

print("Links:")
for link in results["links"]:
    print(link)

