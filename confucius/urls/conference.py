from django.conf.urls.defaults import patterns, url

from confucius.views import ConferenceToggleView, ConferenceUpdateView, MembershipListView

urlpatterns = patterns('confucius.views',
    url(r'^dashboard/$', 'dashboard', name='dashboard'),
    url(r'^dashboard/(?P<conference_pk>\d+)/$', 'dashboard', name='dashboard'),
    url(r'^list/$', MembershipListView.as_view(), name='membership_list'),
    url(r'^update/(?P<pk>\d+)/$', ConferenceUpdateView.as_view(), name='conference_edit'),
    url(r'^toggle/(?P<pk>\d+)/$', ConferenceToggleView.as_view(), name='conference_toggle'),
    url(r'^create_alert/(?P<conference_pk>\d+)/$', 'create_alert', name='create_alert'),
    url(r'^reviewer_invitation/(?P<conference_pk>\d+)/$', 'reviewer_invitation', name='reviewer_invitation'),
    url(r'^reviewer_invitation/(?P<hashCode>.+)$', 'reviewer_response', name='reviewer_response'),
)
