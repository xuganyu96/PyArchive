import os

from django.db import models

#   The directory, relative to the project directory, of the scripts
SCRIPTS_DIR = './scripts'


class AdminTool(models.Model):
    tool_id = models.CharField(max_length=512, primary_key=True)
    tool_title = models.CharField(max_length=1024, null=False)
    tool_description = models.CharField(max_length=1024, null=True)
    deployed = models.BooleanField(default=False)

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
