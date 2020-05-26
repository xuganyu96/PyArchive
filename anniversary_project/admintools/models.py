import os
import subprocess
import time
import multiprocessing as mp
import sys

from django.db import models
from anniversary_project.settings import BASE_DIR

#   The directory, relative to the project directory, of the scripts
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
MANAGE_PATH = os.path.join(BASE_DIR, 'manage.py')


class AdminTool(models.Model):
    tool_id = models.CharField(max_length=512, primary_key=True)
    tool_title = models.CharField(max_length=1024, null=False)
    tool_description = models.CharField(max_length=1024, null=True)
    is_permanent = models.BooleanField(default=False)

    def save_with_script(self, script_str: str):
        """
        :param script_str: a String object that is the actual script
        :return: None; save the model instance, and save the script
        """
        self.save_script(str(self.tool_id), script_str)
        self.save()

    @classmethod
    def save_script(cls, script_name: str, script_str: str, scripts_dir: str = SCRIPTS_DIR):
        """
        :param script_name: the file name that this script will be saved to
        :param script_str: the complete script as a single long string
        :param scripts_dir:
        :return: Nothing; save the scripts to scripts_dir/script_name.py, wrapped in a run() method
        """
        script_path = os.path.join(scripts_dir, f"{script_name}.py")
        script_lines = script_str.splitlines()
        content = ['run():'] + [f"    {script_line}" for script_line in script_lines]
        with open(script_path, 'w') as f:
            f.write('def run():\n')
            for script_line in script_lines:
                f.write(f"    {script_line}\n")

    def delete(self, *args, **kwargs):
        """
        Overwrite the default deletion method so that the script can be deleted together
        """
        script_path = os.path.join(SCRIPTS_DIR, f"{self.tool_id}.py")
        if os.path.isfile(script_path):
            os.remove(script_path)
        super().delete(*args, **kwargs)

    def make_permanent(self):
        """
        Set deployed to True
        """
        self.is_permanent = True
        self.save()

    def run_script(self) -> subprocess.Popen:
        """
        :return:
        """
        cmd = ['python', MANAGE_PATH, 'runscript', str(self.tool_id)]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return proc

    def __str__(self):
        return self.tool_title


class AdminToolDeploymentSchema(models.Model):
    """
    Abstract the recurring running of a single admintool instance
    """
    admintool: AdminTool = models.ForeignKey(to=AdminTool, on_delete=models.CASCADE)
    pid = models.IntegerField(null=True)
    sleep_seconds = models.IntegerField(null=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.p: mp.Process = self.spawn_process()
        self.logger = sys.stdout.write

    def spawn_process(self):
        def recurrent_script_run():
            while True:
                print(f"Starting a run cycle for {self.admintool}")
                proc = self.admintool.run_script()
                stdout_line = True
                while stdout_line:
                    stdout_line = proc.stdout.readline().decode()
                    self.logger(stdout_line)
                print(f"Run cycle finished; sleeping for {self.sleep_seconds} seconds")
                time.sleep(float(self.sleep_seconds))

        p = mp.Process(target=recurrent_script_run)
        return p

    def start(self):
        """
        :return: Start a the repeating process, and record the pid
        """
        self.p.start()
        self.pid = self.p.pid
        self.save()

    def terminate(self):
        """
        :return: call the terminate method and wait until it is terminated; after that update pid to NULL
        """
        self.p.terminate()
        self.p.join()
        self.pid = None
        self.save()
