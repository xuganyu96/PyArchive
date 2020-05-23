import json
import subprocess
import os

from channels.generic.websocket import WebsocketConsumer

from anniversary_project.settings import BASE_DIR


class AdminHomeConsoleConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        tool_id = text_data_json['tool_id']
        django_manage_script_path = os.path.join(BASE_DIR, 'manage.py')
        cmd = ['python', django_manage_script_path, 'runscript', tool_id]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        stdout_line = True
        while stdout_line:
            stdout_line = proc.stdout.readline().decode()
            self.send(text_data=json.dumps({'message': stdout_line}))
