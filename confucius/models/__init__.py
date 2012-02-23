from django.db import models


class ConfuciusModel(models.Model):
    """
    Base class for models which belong to confucius.
    Used mainly to avoid adding a Meta class with the
    right app_label for each model.
    """
    class Meta:
        abstract = True
        app_label = 'confucius'


from confucius.models.account import Address, Email, Language
from confucius.models.conference import (Alert, Conference, Domain, Membership, MessageTemplate, MockUser, Role)
