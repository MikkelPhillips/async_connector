# AsyncConnector - Reliable Asynchronous Internet Connection and Monitoring Class

##  Introduction

```AsyncConnector``` is a Python class designed for sending reliable asynchronous HTTP GET requests to a specified URL. It takes advantage of the aiohttp library for asynchronous HTTP requests and asyncio for handling asynchronous operations. This class is especially useful when working with APIs or scraping large amounts of web data. It also logs information regarding the requests made for monitoring and quality assessment.

## Installation
Requirements
- Python 3.7 or higher.
- aiohttp
- asyncio

## Usage
Here’s a basic example on how to use the AsyncConnector class:

``` python
import asyncio
import aiohttp
from async_connector import AsyncConnector

async def main():
    async with aiohttp.ClientSession() as session:
        connector = AsyncConnector(logfile="logs.csv", overwrite_log=True, n_tries=3, timeout=5)
        response = await connector.get(session, "https://api.example.com/data", "ExampleProject")
        print(response)

asyncio.run(main())
```

## Class Initialisation

You can initialise the ```AsyncConnector``` class as follows:

``` python
connector = AsyncConnector(logfile, overwrite_log, n_tries, timeout)
```

- ```logfile``` (str): The path to the log file where the request logs will be stored.
- ```overwrite_log``` (bool): If True, the log file will be overwritten if it already exists. Otherwise, logs will be appended to the existing file. Default is False.
- ```n_tries``` (int): The number of retries for the GET request in case of connection errors. Default is 10.
- ```timeout``` (int): The number of seconds the GET request will wait for the server to respond. Default is 30.

## Methods

### rate_limit(delay)
Asynchronously waits for a specified number of seconds. Can be used for rate limiting.

#### Parameters
- ```delay``` (float): The number of seconds to wait.

#### Returns
None. 

### get(session, url, project_name)
Sends an asynchronous GET request to the specified URL with error handling and logging.

#### Parameters
- ```session``` (aiohttp.ClientSession object): An aiohttp ClientSession object.
- ```url``` (str): The URL to send a GET request to.
- ```project_name``` (str): The project name used for analyzing the log.

#### Returns
GET request response in JSON format (dict).


## Log Format
The log file will contain the following columns:

- ```call_id```: Unique identifier for each call.
- ```project```: Project name used for analyzing the log.
- ```t```: Time at which the request was made.
- ```delta_t```: Time taken for the request.
- ```url```: The URL to which the request was made.
- ```redirect_url```: The URL to which the request was redirected.
- ```response_size```: Size of the response received.
- ```response_code```: HTTP response code.
- ```success```: Whether the request was successful (True or False).
- ```error```: Error message if the request was unsuccessful.

## License
This project is licensed under the MIT License.