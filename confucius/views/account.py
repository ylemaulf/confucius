from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext

from confucius.forms import AddressFormSet, EmailFormSet, UserForm


@login_required
def edit_account(request, template='account/edit_account.html'):
    import json
    from django.http import HttpResponse

    form = UserForm(instance=request.user)
    address_formset = AddressFormSet(instance=request.user)
    email_formset = EmailFormSet(instance=request.user)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=request.user)
        address_formset = AddressFormSet(request.POST, instance=request.user)
        email_formset = EmailFormSet(request.POST, instance=request.user)

        for f in (form, address_formset, email_formset):
            if f.is_valid():
                f.save()
            else:
                return HttpResponse(json.dumps(f.errors), content_type='text/plain')
        return HttpResponse('', content_type='text/plain')

    context = {
        'address_formset': address_formset,
        'email_formset': email_formset,
        'form': form
    }

    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
def close_account(request):
    from django.contrib.auth import logout

    request.user.is_active = False
    request.user.save()
    logout(request)
    return redirect('login')
