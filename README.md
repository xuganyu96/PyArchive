# PyArchive
In celebration of my anniversary at my first full-time job out of college, I would like to apply what I have learned from
my work, and demonstrate my understanding of software development through a web application.

```bash
docker run \
    -p 8000:8000 \
    --env DJANGO_DEBUG=0 \
    --env DJANGO_SECRET_KEY="GENERATE_YOUR_SECURE_SECRET_KEY_HERE" 
    --name pyarchive 
    --detach 
    pyarchive:latest
```