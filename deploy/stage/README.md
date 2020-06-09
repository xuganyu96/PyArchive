# Deployment to stage
Things about deployment to staging environment will appear here:

Here are a few things that I want to do with the staging environment:
* **Static IP** means that I can terminate the current staging server, spawn a new one, and the URL for SSH and for seeing the website on the staging server will not change
* **Configuring SSH** means that I SSH into the staging server instance with my own SSH keys, not the `.pem` file downloaded from AWS; it also means that I SSH into my own user, not `admin`