import os
import time
import json
import traceback
import aiohttp
import asyncio


class Connector():
    def __init__(self, logfile, overwrite_log=False, n_tries=10, timeout=30):
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

        self.n_tries = n_tries
        self.timeout = timeout
        self.logfilename = logfile

        header = [
            'id',
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
                self.id = 0
            else:
                # Assume id is the first entry in the last line and is an integer
                last_line = lines[-1]
                last_id = last_line.split(';')[0]
                try:
                    self.id = int(last_id) + 1
                except ValueError:
                    self.id = 0

    async def rate_limit(delay):
        """
        Asynchronously waits for a specified number of seconds. Can be used for rate limiting.
        
        :param delay: The number of seconds to wait.
        :type delay: int or float
        """
        await asyncio.sleep(delay)

    async def get(self, session: aiohttp.ClientSession, url: str, project_name: str):
        """
        Method for connector to send asynchronous GET requests reliably to the
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

        for n in range(self.n_tries):
            t_start = time.time()
            try:
                async with session.get(url, timeout=self.timeout) as response:
                    t_end = time.time()
                    r = await response.json()
                    error = ''
                    success = True
                    redirect_url = str(response.url)
                    dt = t_end - t_start
                    size = len(json.dumps(r))
                    response_code = response.status
                    call_id = self.id
                    self.id += 1
                    row = [
                        call_id,
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
                        await rate_limit(self.timeout * n ** 2)
                        continue  # Retry in case of server error

                    self.log.write('\n' + ';'.join(map(str, row)))
                    self.log.flush()

                    return r, response_code, call_id

            except Exception as e:
                t_end = time.time()
                error = traceback.format_exc()
                success = False
                redirect_url = ''
                dt = t_end - t_start
                size = 0
                response_code = ''
                call_id = self.id
                self.id += 1
                row = [
                    call_id,
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

                await rate_limit(self.timeout * n ** 2)  # Assume rate_limit is asynchronous

    def __del__(self):
        """
        Destructor method to clean up resources before the object is destroyed.
        """
        if hasattr(self, 'log') and not self.log.closed:
            self.log.close()
    
