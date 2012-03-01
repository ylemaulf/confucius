from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.forms.models import modelform_factory
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_http_methods

from confucius.decorators import has_chair_role, has_role
from confucius.forms import ConferenceForm, MembershipForm, SendEmailToUsersForm
from confucius.models import Alert, Assignment, Conference, Invitation, Membership, Paper, Role


@require_GET
def conference_access(request, conference_pk, access_key, template_name='conference/membership_form.html'):
    conference = get_object_or_404(Conference, pk=conference_pk, access_key=access_key)

    if request.user.is_authenticated():
        try:
            Membership.objects.get(user=request.user, conference=conference)
            return redirect('dashboard', conference_pk=conference_pk)
        except:
            pass

        return redirect('membership', conference_pk=conference_pk)
    else:
        # We don't handle anonymous users, yet.
        return redirect('login')


@require_http_methods(['GET', 'POST'])
@login_required
@csrf_protect
def membership(request, conference_pk, template_name='conference/membership_form.html'):
    conference = Conference.objects.get(pk=conference_pk)

    try:
        membership = Membership.objects.get(user=request.user, conference=conference)
    except:
        membership = Membership(**{'conference': conference, 'user': request.user})

    form = MembershipForm(instance=membership)

    if 'POST' == request.method:
        form = MembershipForm(request.POST, instance=membership)

        if form.is_valid():
            membership = form.save()
            membership.roles.add(Role.objects.get(code='S'))
            messages.success(request, u'Your membership has been sucessfully updated.')
            return redirect('dashboard', conference_pk=membership.conference.pk)

    context = {
        'form': form,
        'conference': conference,
    }

    return render_to_response(template_name, context, context_instance=RequestContext(request))


@require_http_methods(['GET', 'POST'])
@login_required
@has_chair_role
@csrf_protect
def conference_edit(request, template_name='conference/conference_form.html'):
    
    form = ConferenceForm(instance=request.conference)

    if 'POST' == request.method:
        form = ConferenceForm(request.POST, instance=request.conference)

        if form.is_valid():
            request.conference = form.save()
            messages.success(request, u'The conference "%s" has been successfully updated.' % request.conference)
            return redirect('dashboard')

    context = {
        'conference': request.conference,
        'form': form,
    }

    return render_to_response(template_name, context, context_instance=RequestContext(request))


@require_GET
@login_required
@has_chair_role
def conference_toggle(request):
    conference = request.conference
    conference.is_open = not conference.is_open
    conference.save()
    messages.success(request, u'You have %s the conference %s' % ('opened' if conference.is_open else 'closed', conference.title))
    return redirect(request.META.get('HTTP_REFERER', 'membership_list'))


@require_GET
@login_required
@has_role
def dashboard(request, template_name='conference/dashboard.html'):
    from django.contrib.sites.models import get_current_site

    conference = request.conference
    membership = request.membership

    alerts_trigger = Alert.objects.filter(conference=conference.pk, reminder__isnull=True, action__isnull=True)
    alerts_reminder = Alert.objects.filter(conference=conference.pk, trigger_date__isnull=True, action__isnull=True)
    alerts_action = Alert.objects.filter(conference=conference.pk, trigger_date__isnull=True, reminder__isnull=True)
    user_papers = Paper.objects.filter(conference=conference, submitter=request.user).order_by('-last_update_date')
    user_assignments = Assignment.objects.filter(reviewer=request.user, is_assigned=True)
    conference_reviews = Assignment.objects.filter(paper__conference=conference, is_done=True, review__isnull=False).order_by('-review__last_update_date')
    conference_papers = Paper.objects.filter(conference=conference).order_by('-submission_date')

    context = {
        'alerts_trigger': alerts_trigger,
        'alerts_reminder': alerts_reminder,
        'alerts_action': alerts_action,
        'conference': conference,
        'membership': membership,
        'user_papers': user_papers,
        'conference_papers': conference_papers,
        'user_assignments': user_assignments,
        'conference_reviews': conference_reviews,
        'public_url': 'http://%s%s' % (get_current_site(request).domain, conference.get_absolute_url())
    }

    return render_to_response(template_name, context, context_instance=RequestContext(request))


@require_GET
def conference_invitation(request, key, decision, template_name='conference/invitation.html'):
    invitation = get_object_or_404(Invitation, key=key)

    if not invitation.pending():
        return redirect('already_answered')

    if decision == 'refuse':
        invitation.refuse()
        return redirect('refusal')

    if not invitation.user.is_active:
        return redirect('signup', key=key)

    invitation.accept()

    try:
        membership = Membership.objects.get(user=invitation.user, conference=invitation.conference)
    except:
        membership = Membership.objects.create(user=invitation.user, conference=invitation.conference)

    membership.roles.clear()
    membership.roles.add(invitation.roles.all())

    messages.success(request, u'You are now participating in the conference "%s"' % invitation.conference)
    return redirect('dashboard', conference_pk=invitation.conference.pk)


@require_http_methods(['GET', 'POST'])
@login_required
@has_chair_role
def conference_invite(request, template_name='conference/invitation_form.html'):
    from confucius.forms import InvitationForm

    form = InvitationForm()

    if 'POST' == request.method:
        instance = Invitation(conference=request.conference)
        form = InvitationForm(request.POST, instance=instance)

        if form.is_valid():
            invitation = form.save(request)
            messages.success(request, u'An invitation has been sent to "%s".' % invitation.user)
            return redirect('dashboard')

    context = {
        'form': form,
        'conference': request.conference,
    }

    return render_to_response(template_name, context, context_instance=RequestContext(request))


@require_GET
@login_required
def membership_list(request, template_name='conference/membership_list.html'):
    membership_list = Membership.objects.filter(user=request.user)

    context = {
        'membership_list': membership_list,
    }

    return render_to_response(template_name, context, context_instance=RequestContext(request))


@require_http_methods(['GET', 'POST'])
@csrf_protect
def signup(request, key, template_name='registration/signup_form.html'):
    from django.contrib.auth import authenticate, login
    from django.db.models import Q
    from confucius.forms import PaperForm, SignupForm

    if request.user.is_authenticated():  # You're already registered, what the fuck would you signup for?
        return redirect('dashboard')

    invitation = get_object_or_404(Invitation, key=key)

    try:
        invitation.roles.get(Q(code='R') | Q(code='C'))
        instance = Membership(**{'conference': invitation.conference, 'user': invitation.user})
        extra_form_class = MembershipForm
    except:
        instance = Paper(**{'conference': invitation.conference, 'submitter': invitation.user})
        extra_form_class = PaperForm

    form = SignupForm(instance=invitation.user)
    extra_form = extra_form_class(instance=instance)

    if request.method == 'POST':
        form = SignupForm(request.POST, instance=invitation.user)
        extra_form = extra_form_class(request.POST, request.FILES, instance=instance)

        for f in (form, extra_form):
            if f.is_valid():
                f.save()

        if not form.errors and not extra_form.errors:
            invitation.accept()
            user = authenticate(username=invitation.user.email, password=form.cleaned_data.get('password1'))
            login(request, user)
            # Add roles
            membership = Membership.objects.get(user=invitation.user, conference=invitation.conference)
            for role in invitation.roles.all():
                membership.roles.add(role)
            membership.save()
            messages.success(request, u'Congratulations! Welcome to the conference.')
            return redirect('dashboard', invitation.conference.pk)

    context = {
        'form': form,
        'extra_form': extra_form,
        'invitation': invitation,
    }

    return render_to_response(template_name, context, context_instance=RequestContext(request))


@login_required
@has_chair_role
@csrf_protect
def send_email_to_users(request, template_name='conference/send_email_to_users.html'):

    conference = request.conference
    form = SendEmailToUsersForm(initial={'conference': conference})

    if 'POST' == request.method:
        form = SendEmailToUsersForm(request.POST, initial={'conference': conference})

        if form.is_valid():
            #Get the cleaned_data from FORM and then send the email
            title = form.cleaned_data['title']
            content = form.cleaned_data['content']
            receivers = form.cleaned_data['receivers']

            for receiver in receivers:
                email = receiver.email
                try:
                    send_mail(title, content, 'no-reply-alerts@confucius.com', [unicode(email)], fail_silently=False)

                except:
                    messages.error(request, u'An error occured during the email sending process. The SMTP settings may be uncorrect, or the receiver(%s) email address may not exist\n' % str(email))
                    return redirect('dashboard')

            messages.success(request, u'You succesfully have just sent your email to the receiver(s)')
            return redirect('dashboard')

    context = {
        'form': form,
        'conference': conference
    }

    return render_to_response(template_name, context, context_instance=RequestContext(request))
