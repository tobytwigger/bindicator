import http.client as httplib
import subprocess
from threading import Thread


class Wifi:

    def __init__(self):
        self._is_connecting = False
        self._wps_thread = None

    def is_connected(self):

        conn = httplib.HTTPSConnection("8.8.8.8", timeout=5)
        try:
            conn.request("HEAD", "/")
            return False
        except Exception:
            return True
        finally:
            conn.close()

    def is_connecting(self):
        return self._is_connecting

    def connect(self):
        self._is_connecting = True

        # Connect to wifi
        # Write me a script that uses the following bash command to connect to wifi
        # wpa_cli wps_pbc
        if(self._wps_thread is None or self._wps_thread.is_alive() is False):
            self._wps_thread = Thread(target=self._run_connection())
            self._wps_thread.start()


    def _run_connection(self):
        subprocess.Popen('sudo wpa_cli wps_pbc', shell=True)

        self._is_connecting = False

        return