"""
iperf3 integration for active throughput testing during WiFi monitoring
"""

import subprocess
import threading
import time
from typing import Optional


class IPerf3Runner:
    """
    Manages iperf3 test execution during WiFi monitoring sessions
    """

    def __init__(self, server: str, port: int = 5201, parallel: int = 1,
                 reverse: bool = False, udp: bool = False):
        """
        Initialize iperf3 runner

        Args:
            server: iperf3 server IP or hostname
            port: Server port (default: 5201)
            parallel: Number of parallel streams (-P flag)
            reverse: Reverse mode - server sends to client (-R flag)
            udp: Use UDP instead of TCP (-u flag)
        """
        self.server = server
        self.port = port
        self.parallel = parallel
        self.reverse = reverse
        self.udp = udp
        self.process = None
        self.thread = None
        self.running = False

    def build_command(self, duration: int = 300) -> list:
        """
        Build iperf3 command with specified parameters

        Args:
            duration: Test duration in seconds

        Returns:
            list: Command arguments
        """
        cmd = [
            'iperf3',
            '-c', self.server,
            '-p', str(self.port),
            '-t', str(duration),
            '-i', '4',  # Report interval matches WiFi sample interval
        ]

        # Add parallel streams if specified
        if self.parallel > 1:
            cmd.extend(['-P', str(self.parallel)])

        # Add reverse mode if specified
        if self.reverse:
            cmd.append('-R')

        # Add UDP mode if specified
        if self.udp:
            cmd.append('-u')
            # For UDP, set a reasonable bandwidth (adjust as needed)
            cmd.extend(['-b', '1000M'])

        return cmd

    def start(self, duration: int = 300):
        """
        Start iperf3 test in background

        Args:
            duration: Test duration in seconds
        """
        if self.running:
            print("WARNING: iperf3 already running")
            return

        cmd = self.build_command(duration)

        def run_iperf():
            try:
                print(f"\n[iperf3] Starting: {' '.join(cmd)}")
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                self.running = True

                # Wait for process to complete
                stdout, stderr = self.process.communicate()

                # Print final results
                if self.process.returncode == 0:
                    print("\n[iperf3] Test completed successfully")
                    # Print last few lines (summary)
                    lines = stdout.strip().split('\n')
                    print("\n[iperf3] Results:")
                    for line in lines[-5:]:
                        print(f"  {line}")
                else:
                    print(f"\n[iperf3] Test failed with code {self.process.returncode}")
                    if stderr:
                        print(f"[iperf3] Error: {stderr}")

            except FileNotFoundError:
                print("\n[iperf3] ERROR: iperf3 not found. Install with: brew install iperf3")
            except Exception as e:
                print(f"\n[iperf3] ERROR: {e}")
            finally:
                self.running = False

        # Start iperf3 in background thread
        self.thread = threading.Thread(target=run_iperf, daemon=True)
        self.thread.start()

        # Give it a moment to start
        time.sleep(1)

    def stop(self):
        """Stop iperf3 test if running"""
        if self.process and self.running:
            print("\n[iperf3] Stopping test...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.running = False

    def is_running(self) -> bool:
        """Check if iperf3 is currently running"""
        return self.running

    @staticmethod
    def check_iperf3_installed() -> bool:
        """
        Check if iperf3 is installed

        Returns:
            bool: True if iperf3 is available
        """
        try:
            result = subprocess.run(
                ['iperf3', '--version'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def test_server_connection(server: str, port: int = 5201, timeout: int = 3) -> bool:
        """
        Test if iperf3 server is reachable

        Args:
            server: Server IP or hostname
            port: Server port
            timeout: Connection timeout in seconds

        Returns:
            bool: True if server is reachable
        """
        try:
            # Try a very short test to verify connectivity
            result = subprocess.run(
                ['iperf3', '-c', server, '-p', str(port), '-t', '1'],
                capture_output=True,
                timeout=timeout + 2,
                text=True
            )
            # Check if it connected (even if test ran)
            return 'Connecting to host' in result.stdout or result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
