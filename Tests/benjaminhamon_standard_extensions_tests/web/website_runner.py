import asyncio
import datetime
import os
import subprocess
import time
from typing import Dict, List, Optional

import requests


class WebsiteRunner:


    def __init__(self, command: List[str], address: str, port: int, environment: Optional[Dict[str,str]] = None) -> None:
        self.command = command
        self.address = address
        self.port = port
        self.environment = environment

        self.timeout = datetime.timedelta(seconds = 10)

        self._process = None


    async def __aenter__(self) -> "WebsiteRunner":
        await self.start()
        return self


    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.stop()


    def get_url(self) -> str:
        return "http://" + self.address + ":" + str(self.port)


    async def start(self) -> None:
        if self._process is not None:
            raise RuntimeError("Website process is already running")

        new_environment = os.environ.copy()
        if self.environment is not None:
            new_environment.update(self.environment)

        try:
            self._process = await asyncio.create_subprocess_exec(*self.command, env = new_environment, stdin = subprocess.DEVNULL)
        except subprocess.CalledProcessError as exception:
            raise RuntimeError("Website process failed to start") from exception

        await self._wait_until_available()


    async def _wait_until_available(self) -> None:
        if self._process is None:
            raise ValueError("process must not be none")

        start_time = time.time()

        while True:
            now = time.time()
            if now > start_time + self.timeout.total_seconds():
                raise TimeoutError("Waiting for website to be available timed out")

            if self._process.returncode is not None:
                raise RuntimeError("Process exited (ExitCode: %s)" % self._process.returncode)

            try:
                response = requests.request("HEAD", self.get_url() + "/", timeout = self.timeout.total_seconds())
                response.raise_for_status()
            except requests.RequestException:
                await asyncio.sleep(1)
                continue

            break


    async def stop(self) -> None:
        if self._process is None:
            raise RuntimeError("Website process is not running")

        if self._process.returncode is None:
            self._process.terminate()

            try:
                await asyncio.wait_for(self._process.wait(), self.timeout.total_seconds())
            except asyncio.TimeoutError:
                pass

        if self._process.returncode is None:
            self._process.kill()

            try:
                await asyncio.wait_for(self._process.wait(), self.timeout.total_seconds())
            except asyncio.TimeoutError:
                pass

        if self._process.returncode is None:
            raise RuntimeError("Website process failed to stop")

        self._process = None
