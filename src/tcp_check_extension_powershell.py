import os
from subprocess import run, PIPE
from typing import Dict
from concurrent.futures import ThreadPoolExecutor

from ruxit.api.base_plugin import BasePlugin
from ruxit.api.selectors import HostSelector

class TCPCheckPowershellExtension(BasePlugin):

    def query(self, **kwargs):
        raw_targets: str = self.config.get("targets")

        with ThreadPoolExecutor(max_workers=10) as worker:
            for line in raw_targets.splitlines():
                self.logger.info(f"Processing line: {line}")
                host, port = line.split(":")
                worker.submit(self.run_test, host, port)

    def run_test(self, host: str, port: str):
        result = test_port(host, port)
        self.logger.info(f"Result for {host}:{port}: {result}")

        self.results_builder.state_metric("tcp_state", result["State"], entity_selector=HostSelector(),
                                          dimensions={"Target": f"{host}:{port}"})

        # send event
        if result["State"] == "ERROR":
            self.results_builder.report_error_event(f"Error running test for {host}:{port}: {result['State']}",
                                                    "Powershell TCP Check Error",
                                                    properties=result)


def test_port(ip: str, port: str) -> Dict[str, str]:
    dictionary = {}
    current_file_path = os.path.dirname(os.path.realpath(__file__))
    script_path = os.path.join(current_file_path, "scripts", "tcp_check.ps1")
    # We need to run the powershell script
    command = ["powershell", "-File", script_path, "-IP", ip, "-Port", port]

    command_result = run(command, stdout=PIPE, stderr=PIPE)
    for line in command_result.stdout.decode().splitlines():
        key, value = line.split(":")
        dictionary[key] = value

    return dictionary