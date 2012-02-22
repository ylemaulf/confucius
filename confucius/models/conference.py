from django.contrib.auth.models import User
from django.db import models

from confucius.models import ConfuciusModel


class Alert(ConfuciusModel):
    title = models.CharField(max_length=100, default=None)
    date = models.DateField()
    content = models.TextField(default=None)
    conference = models.ForeignKey('Conference')

    class Meta(ConfuciusModel.Meta):
        unique_together = ('title', 'conference',)

    def __unicode__(self):
        return self.title


class Conference(ConfuciusModel):
    title = models.CharField(max_length=100, unique=True)
    is_open = models.BooleanField(default=False)
    start_date = models.DateField()
    submissions_start_date = models.DateField()
    submissions_end_date = models.DateField()
    reviews_start_date = models.DateField()
    reviews_end_date = models.DateField()
    url = models.URLField(blank=True)
    members = models.ManyToManyField(User, through='Membership')
    domains = models.ManyToManyField('Domain')

    def __unicode__(self):
        return self.title


class Domain(ConfuciusModel):
    name = models.CharField(max_length=50, unique=True)

    def __unicode__(self):
        return self.name


class Membership(ConfuciusModel):
    user = models.ForeignKey(User)
    conference = models.ForeignKey(Conference)
    roles = models.ManyToManyField('Role')
    domains = models.ManyToManyField(Domain)

    class Meta(ConfuciusModel.Meta):
        unique_together = ('user', 'conference')


class MessageTemplate(ConfuciusModel):
    title = models.CharField(max_length=100, default=None)
    content = models.TextField(default=None)
    conference = models.ForeignKey(Conference)

    class Meta(ConfuciusModel.Meta):
        unique_together = ('title', 'conference')

    def __unicode__(self):
        return self.title


class Role(ConfuciusModel):
    code = models.CharField(max_length=1)
    name = models.CharField(max_length=9)

    def __unicode__(self):
        return self.name
