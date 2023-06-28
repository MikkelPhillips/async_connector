import os
import time
import json
import traceback
import aiohttp
import asyncio


class AsyncConnector():
    """
    This class implements a method for reliable connection to the internet
    and monitoring. It handles simple errors due to connection problems,
    and logs a range of information for basic quality assessments.

    :param logfile: path to log file
    :type logfile: str

    :param overwrite_log: define if logfile should be cleared
    :type overwrite_log: bool

    :param n_tries: defines the number of retries the *get* method will
    have in order to avoid connection errors.
    :type n_tries: int

    :param timeout: seconds the get request will wait for the server to
    respond in order to avoid connection errors.
    :type timeout: int
    """

    def __init__(self, logfile: str, overwrite_log=False, n_tries=10, timeout=30):

        self.n_tries = n_tries
        self.timeout = timeout
        self.logfilename = logfile

        header = [
            'call_id',
            'project',
            't',
            'delta_t',
            'url',
            'redirect_url',
            'response_size',
            'response_code',
            'success',
            'error'
        ]

        if os.path.isfile(logfile):
            # If the log file already exists then check to see if the file should
            # be overwritten else append to the existing file
            if overwrite_log:
                self.log = open(logfile, 'w')
                self.log.write(';'.join(header) + '\n')
                self.log.flush()
            else:
                self.log = open(logfile, 'a')
        else:
            self.log = open(logfile, 'w')
            self.log.write(';'.join(header) + '\n')
            self.log.flush()

        # Read the file to determine the next call id
        with open(logfile, 'r') as f:
            lines = f.readlines()
            if len(lines) <= 1:
                self.call_id = 0
            else:
                # Assume id is the first entry in the last line and is an integer
                last_line = lines[-1]
                last_id = last_line.split(';')[0]
                try:
                    self.call_id = int(last_id) + 1
                except ValueError:
                    self.call_id = 0

    @staticmethod
    async def rate_limit(delay: float):
        """
        Asynchronously waits for a specified number of seconds. Can be used for rate limiting.
        
        :param delay: The number of seconds to wait.
        :type delay: float
        """
        await asyncio.sleep(delay)

    async def get(self, session: aiohttp.ClientSession, url: str, project_name: str):
        """
        Method for Asyncconnector to send asynchronous GET requests reliably to the
        internet, with multiple tries and simple error handling, as well as a
        simple logging function.

        :param session: aiohttp.ClientSession object
        :type session: aiohttp.ClientSession object

        :param url: url to send a get request
        :type url: str

        :param project_name: Name used for analyzing the log.
        :type project_name: str

        :return: GET request response in JSON format
        :rtype: dict
        """

        for _ in range(self.n_tries):
            t_start = time.time()
            try:
                async with session.get(url, timeout=self.timeout) as response:
                    t_end = time.time()
                    #r = await response.json()
                    error = ''
                    success = True
                    redirect_url = str(response.url)
                    dt = t_end - t_start
                    #size = len(json.dumpr(r))
                    response_code = response.status
                    current_call_id = self.call_id
                    self.call_id += 1

                    content_type = response.headers.get('Content-Type')
                    if 'json' in content_type:
                        r = await response.json()
                        size = len(json.dumps(r))
                    else:
                        # Handle non-JSON response
                        r = await response.text()
                        size = len(r)

                    row = [
                        current_call_id,
                        project_name,
                        t_start,
                        dt,
                        url,
                        redirect_url,
                        size,
                        response_code,
                        success,
                        error
                    ]

                    if response_code >= 500:
                        await AsyncConnector.rate_limit(self.timeout)
                        continue  # Retry in case of server error

                self.log.write('\n' + ';'.join(map(str, row)))
                self.log.flush()

                return r

            except aiohttp.ClientConnectionError:
                error = "Connection error"
                success = False

            except asyncio.TimeoutError:
                error = "Timeout error"
                success = False

            except Exception as e:
                error = traceback.format_exc()
                success = False

            finally:
                t_end = time.time()
                redirect_url = ''
                dt = t_end - t_start
                size = 0
                response_code = ''
                current_call_id = self.call_id
                self.call_id += 1
                row = [
                    current_call_id,
                    project_name,
                    t_start,
                    dt,
                    url,
                    redirect_url,
                    size,
                    response_code,
                    success,
                    error
                ]
                self.log.write('\n' + ';'.join(map(str, row)))
                self.log.flush()

                await AsyncConnector.rate_limit(self.timeout)

    def __del__(self):
        """
        Destructor method to clean up resources before the object is destroyed.
        """
        if hasattr(self, 'log') and not self.log.closed:
            self.log.close()