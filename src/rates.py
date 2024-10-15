import requests
import time

# GitHub API endpoint for rate limit
url = 'https://api.github.com/rate_limit'

# Make the GET request to the rate limit endpoint
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()["resources"]["core"]
    resetTime = response.json()["resources"]["core"]["reset"]
    print("Rate limit data:", data)
    print(f"Resets on: {time.ctime(resetTime)}")
else:
    print(f"Failed to fetch data, status code: {response.status_code}")