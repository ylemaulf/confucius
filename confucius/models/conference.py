from django.db import models

from confucius.models import ConfuciusModel, User


class Action(ConfuciusModel):
    name = models.CharField(max_length=155, verbose_name='Action')

    def __unicode__(self):
        return self.name


class Alert(ConfuciusModel):
    title = models.CharField(max_length=100, default=None)
    content = models.TextField(default=None)
    conference = models.ForeignKey('Conference')
    trigger_date = models.DateField(verbose_name='trigger date', blank=True, null=True)
    reminder = models.ForeignKey('Reminder', blank=True, null=True)
    event = models.ForeignKey('Event', blank=True, null=True)
    action = models.ForeignKey('Action', blank=True, null=True)
    roles = models.ManyToManyField('Role', blank=True)

    class Meta(ConfuciusModel.Meta):
        unique_together = ('title', 'conference',)

    def __unicode__(self):
        return self.title


class Conference(ConfuciusModel):
    title = models.CharField(max_length=100, unique=True)
    is_open = models.BooleanField(default=False)
    has_finalize_paper_selections = models.BooleanField(default=False)
    start_date = models.DateField()
    submissions_start_date = models.DateField()
    submissions_end_date = models.DateField()
    reviews_start_date = models.DateField()
    reviews_end_date = models.DateField()
    url = models.URLField(blank=True)
    members = models.ManyToManyField(User, through='Membership')
    domains = models.ManyToManyField('Domain', related_name='conferences')
    access_key = models.CharField(max_length=8)

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('confucius.views.conference_access', (),
            {'conference_pk': self.pk, 'access_key': self.access_key})

    def save(self, *args, **kwargs):
        from confucius.utils import random_string

        if self.pk is None:
            self.access_key = random_string(8)

        super(Conference, self).save(*args, **kwargs)


class Domain(ConfuciusModel):
    name = models.CharField(max_length=50, unique=True)

    def __unicode__(self):
        return self.name


class Event(ConfuciusModel):
    name = models.CharField(max_length=155, verbose_name='linked to')

    def __unicode__(self):
        return self.name


class Membership(ConfuciusModel):
    user = models.ForeignKey(User, related_name='memberships')
    conference = models.ForeignKey(Conference)
    roles = models.ManyToManyField('Role')
    domains = models.ManyToManyField(Domain)
    last_accessed = models.BooleanField(default=False)

    class Meta(ConfuciusModel.Meta):
        unique_together = ('user', 'conference')

    def set_last_accessed(self):
        Membership.objects.filter(user=self.user).update(last_accessed=False)
        self.last_accessed = True
        self.save()

    def _has_role(self, code):
        try:
            self.roles.get(code=code)
            return True
        except:
            return False

    def has_chair_role(self):
        return self._has_role('C')

    def has_reviewer_role(self):
        return self._has_role('R')

    def has_submitter_role(self):
        return self._has_role('S')
        

class MessageTemplate(ConfuciusModel):
    title = models.CharField(max_length=100, default=None)
    content = models.TextField(default=None)
    conference = models.ForeignKey(Conference)

    class Meta(ConfuciusModel.Meta):
        unique_together = ('title', 'conference')

    def __unicode__(self):
        return self.title


class Reminder(ConfuciusModel):
    value = models.PositiveIntegerField()
    name = models.CharField(max_length=155, verbose_name='reminder')

    class Meta(ConfuciusModel.Meta):
        unique_together = ('value', 'name')

    def __unicode__(self):
        return self.name


class Role(ConfuciusModel):
    code = models.CharField(max_length=1)
    name = models.CharField(max_length=9)

    def __unicode__(self):
        return self.name


class Invitation(ConfuciusModel):
    user = models.ForeignKey(User)
    conference = models.ForeignKey(Conference)
    roles = models.ManyToManyField(Role)
    decision = models.CharField(max_length=1, choices=(
        ('A', 'Accepted'),
        ('R', 'Refused'),
        ('W', 'Waiting for response')
    ), default='W')
    key = models.CharField(max_length=64, unique=True)
    message = models.TextField()

    class Meta(ConfuciusModel.Meta):
        unique_together = ('user', 'conference')

    def _decision(self, code):
        self.decision = code
        self.save()

    def pending(self):
        return self.decision == 'W'

    def refuse(self):
        self._decision('R')

    def accept(self):
        self._decision('A')
