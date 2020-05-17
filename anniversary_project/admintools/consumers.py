import json
import subprocess
import tempfile

from channels.generic.websocket import WebsocketConsumer


class AdminConsoleConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        script_text = text_data_json['script_text']
        with tempfile.NamedTemporaryFile() as tmp:
            with open(tmp.name, 'w') as f:
                f.write(script_text)
            cmd = ['python', tmp.name]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            stdout_line = True
            while stdout_line:
                stdout_line = proc.stdout.readline().decode()
                self.send(text_data=json.dumps({'message': stdout_line}))
