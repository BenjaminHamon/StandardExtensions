import asyncio
import subprocess
import sys

import requests


class WebsiteRunner:

    def __init__(self, script_path: str, address: str, port: int) -> None:
        self.script_path = script_path
        self.address = address
        self.port = port

        self.timeout_seconds = 5

        self._process = None


    async def __aenter__(self) -> "WebsiteRunner":
        await self.start()
        return self


    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.stop()


    async def start(self) -> None:
        if self._process is not None:
            raise RuntimeError("Website process is already running")

        command = [ sys.executable, self.script_path, "--address", self.address, "--port", str(self.port) ]

        try:
            self._process = await asyncio.create_subprocess_exec(*command, stdin = subprocess.DEVNULL)
        except subprocess.CalledProcessError as exception:
            raise RuntimeError("Website process failed to start") from exception

        # The method check_is_running can fail if called too quickly, only on Linux apparently.
        # This sleep should not be necessary as there should be request retries, but for reason it fails regardless.
        await asyncio.sleep(0.5)

        self.check_is_running()


    def get_url(self) -> str:
        return "http://" + self.address + ":" + str(self.port)


    def check_is_running(self) -> None:
        if self._process is None or self._process.returncode is not None:
            raise RuntimeError("Website process is not running")

        try:
            response = requests.request("GET", self.get_url() + "/", timeout = self.timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as exception:
            raise RuntimeError("Website is not reachable") from exception


    async def stop(self) -> None:
        if self._process is None:
            raise RuntimeError("Website process is not running")

        if self._process.returncode is None:
            self._process.terminate()

            try:
                await asyncio.wait_for(self._process.wait(), self.timeout_seconds)
            except asyncio.TimeoutError:
                pass

        if self._process.returncode is None:
            self._process.kill()

            try:
                await asyncio.wait_for(self._process.wait(), self.timeout_seconds)
            except asyncio.TimeoutError:
                pass

        if self._process.returncode is None:
            raise RuntimeError("Website process failed to stop")

        self._process = None
