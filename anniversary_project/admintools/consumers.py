import json
import subprocess
import os
import tempfile
import uuid

from channels.generic.websocket import WebsocketConsumer

from anniversary_project.settings import BASE_DIR
from .models import AdminTool

MANAGE_PATH = os.path.join(BASE_DIR, 'manage.py')


class AdminHomeConsoleConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        tool_id = text_data_json['tool_id']
        tool: AdminTool = AdminTool.objects.get(tool_id=tool_id)
        proc = tool.run_script()

        stdout_line = True
        while stdout_line:
            stdout_line = proc.stdout.readline().decode()
            self.send(text_data=json.dumps({'message': stdout_line}))


class AdminDevelopConsoleConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.temp_tool_id = str(uuid.uuid4())

    def connect(self):
        """
        Upon connection, create a dummy admin tool
        """
        self.accept()
        temp_tool = AdminTool(
            tool_id=self.temp_tool_id,
            tool_title='Temp'
        )
        temp_tool.save()

    def disconnect(self, close_code):
        """
        Upon disconnection, delete the dummy admin tool
        """
        temp_tool = AdminTool.objects.get(tool_id=self.temp_tool_id)
        temp_tool.delete()

    def receive(self, text_data=None, bytes_data=None):
        """
        Upon receiving a message, save it under the temporary admin tool, then run it
        """
        text_data_json = json.loads(text_data)
        script_text = text_data_json['script_text']
        temp_tool: AdminTool = AdminTool.objects.get(tool_id=self.temp_tool_id)
        temp_tool.save_with_script(script_text)
        cmd = ['python', MANAGE_PATH, 'runscript', temp_tool.tool_id]
        proc = temp_tool.run_script()
        stdout_line = True
        while stdout_line:
            stdout_line = proc.stdout.readline().decode()
            self.send(text_data=json.dumps({'message': stdout_line}))
