from django.db import models
from django.contrib.auth.models import User
from django.db.models.fields.files import ImageFieldFile
from PIL import Image


class Profile(models.Model):
    user: User = models.OneToOneField(User, on_delete=models.CASCADE)
    image: ImageFieldFile = models.ImageField(default='default.png', upload_to='profile_pics')

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        #   Method signature included **kwargs because it needs to somewhat match with parent class' save() method
        """
        Overwrite the existing save method so we can modify the saving behavior:
        """
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)