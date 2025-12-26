from django.db import models


class CartManager(models.Manager):
    def get_or_create_by_session(self, session_key):
        cart, created = self.get_or_create(session_key=session_key)
        return cart, created

