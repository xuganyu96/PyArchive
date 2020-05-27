import os
import subprocess
import time
import multiprocessing as mp
import psutil
import logging

from django.db import models
from anniversary_project.settings import BASE_DIR

#   The directory, relative to the project directory, of the scripts
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
MANAGE_PATH = os.path.join(BASE_DIR, 'manage.py')
deployment_logger = logging.getLogger('admintools_deployment')
file_handler = logging.FileHandler(os.path.join(BASE_DIR, 'log/system.log'))
console_handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
deployment_logger.addHandler(file_handler)
deployment_logger.addHandler(console_handler)
deployment_logger.setLevel(logging.INFO)


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
        self.logger = self.get_logger()
        self.p: mp.Process = self.spawn_process()

    def get_logger(self):
        """
        :return: a function that takes a string and log it
        """
        logger = logging.getLogger(name=f"admintools_deployment.{self.pk}")
        logger.propagate = True
        return logger.info

    def spawn_process(self):
        def recurrent_script_run(logger):
            while True:
                proc = self.admintool.run_script()
                stdout_line = True
                while stdout_line:
                    stdout_line = proc.stdout.readline().decode()[:-1]
                    if stdout_line:
                        logger(f"<{self.admintool.tool_id}>.py: " + stdout_line)
                time.sleep(float(self.sleep_seconds))

        p = mp.Process(target=recurrent_script_run, kwargs={'logger': self.logger})
        return p

    def start(self):
        """
        :return: Start a the repeating process, and record the pid
        """
        self.logger(f"Starting {self.admintool} running every {self.sleep_seconds} seconds")
        self.p.start()
        self.pid = self.p.pid
        self.save()

    def terminate(self):
        """
        :return: call the terminate method and wait until it is terminated; after that update pid to NULL
        """
        if self.pid:
            self.logger(f"Terminating deployment {self.pk} with PID {self.pid}")
            try:
                p = psutil.Process(self.pid)
                p.terminate()
                self.logger(f"Deployment {self.pk} with PID {self.pid} terminated")
            except:
                pass
        self.pid = None
        self.save()

    def delete(self, *args, **kwargs):
        """
        Overwrite the default deletion method to add a step that closes the process
        """
        self.terminate()
        self.p.close()
        super().delete(*args, **kwargs)
