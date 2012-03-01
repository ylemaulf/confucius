from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_http_methods
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext

from confucius.decorators import has_chair_role
from confucius.models import Alert


@require_http_methods(['GET', 'POST'])
@login_required
@has_chair_role
@csrf_protect
def alert(request, alert_pk=None, template_name='conference/alert/alert_form.html'):
    from confucius.forms import AlertForm

    instance = Alert(**{'conference_id': request.conference.pk})

    if alert_pk is not None:
        instance = get_object_or_404(Alert, pk=alert_pk, conference=request.conference)

    form = AlertForm(instance=instance)

    if 'POST' == request.method:
        form = AlertForm(request.POST, instance=instance)

        if form.is_valid():
            form.save()
            messages.success(request, u'The alert "%s" has been successfully %s.' % (instance, 'created' if alert_pk is None else 'updated'))
            return redirect('dashboard')

    context = {
        'form': form,
        'alert':instance,
        'conference':request.conference,
    }

    return render_to_response(template_name, context, context_instance=RequestContext(request))


@require_GET
@login_required
@has_chair_role
def delete_alert(request, alert_pk):
    alert = get_object_or_404(Alert, pk=alert_pk, conference=request.conference)
    alert.delete()
    messages.success(request, u'The alert "%s" has been successfully deleted.' % alert)

    return redirect('dashboard')
