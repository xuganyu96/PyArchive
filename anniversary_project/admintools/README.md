# Admintools page layouts:
* A home page at `/admintools/home` with a center console for displaying output, a number of cards each of which having 
a title, a brief description, and a `run` button. Each card corresponds to an instance of an `AdminTool` model.
* A detail page  at `/admintools/tool/<tool_id>` for each of the `AdminTool` instance. In the detail page, show a title, 
a center console for displaying output, and the source code in a text box at the bottom.
* A "Develop" page at `/admintools/develop` with a textbox input at the top, three buttons `run`, `reset`, and `deploy`,
and a console output text box at the bottom. The textbox on the top is writable; the textbox on the bottom is read-only.
THe top textbox is meant for entering Python code; if the run button is clicked (or ctrl + enter), then the output of 
the script should be displayed on the console at the bottom, line by line. If reset button is clicked, then clear both 
textboxes. If the deploy button is clicked, then redirect to the "Deploy" page
* A "Deploy" page at `/admintools/deploy` with a read-only textbox for displaying script source code, a few more boxes
for filling in `machine-name`, `display-title`, `display-description`, etc., a `cancel` button, and a `deploy` button.
The cancel button will redirect to `/admintools/home`; the `deploy` button will save the script source code to a script
named `<machine-name>.py` under `scripts`, and save an instance of `AdminTool` model with the forms filled out.