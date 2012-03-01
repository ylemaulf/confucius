from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin

from confucius.forms import AddressFormSet, EmailFormSet, UserCreationForm, UserForm
from confucius.models import Assignment, Address, Conference, Domain, Email, Membership, Paper, User, Language


class AdminConferenceForm(forms.ModelForm):
    class Meta:
        model = Conference
        exclude = ('access_key')


class AdminUserForm(UserForm):
    class Meta(UserForm.Meta):
        fields = ('email', 'first_name', 'is_active', 'is_superuser', 'languages', 'last_name')


class AddressInline(admin.StackedInline):
    extra = 0
    formset = AddressFormSet
    model = Address


class EmailInline(admin.StackedInline):
    extra = 0
    formset = EmailFormSet
    model = Email


class UserAdmin(AuthUserAdmin):
    actions = ['activate', 'deactivate']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2')}
        ),
    )
    fieldsets = (
        (None, {
            'fields': ('is_active', 'password')
        }),
        ('Personal information', {
            'fields': (('first_name', 'last_name'),)
        }),
        ('Languages', {
            'classes': ('collapse',),
            'fields': ('languages',)
        })
    )
    filter_horizontal = ()
    form = AdminUserForm
    inlines = [AddressInline, EmailInline]
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_superuser')
    list_display_links = ('email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_superuser', 'date_joined')
    ordering = ()
    readonly_fields = ('password', )
    search_fields = ('email', 'first_name', 'last_name')

    def update_is_active(self, request, queryset, is_active):
        rows_updated = queryset.update(is_active=is_active)

        if rows_updated == 1:
            message_bit = '1 user was'
        else:
            message_bit = '%s users were' % rows_updated

        self.message_user(request, "%s successfully %s." % (message_bit, 'activated' if is_active else 'deactivated'))

    def activate(self, request, queryset):
        self.update_is_active(request, queryset, True)

    def deactivate(self, request, queryset):
        self.update_is_active(request, queryset, False)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs.update({'form': UserCreationForm})

        return super(UserAdmin, self).get_form(request, obj, **kwargs)

    def get_formsets(self, request, obj=None, **kwargs):
        for inline in self.inline_instances:
            if obj is None:
                continue
            yield inline.get_formset(request, obj)


class PaperAdmin(admin.ModelAdmin):
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('title', 'language', 'submitter', 'conference', 'co_authors', 'file',)}
        ),
    )
    fieldsets = (
        ('Paper information', {
            'fields': (('title', 'language', 'domains'), )
        }),
        ('Authors information', {
            'fields': (('submitter', 'conference',), 'co_authors', )
        }),
        ('Date information', {
            'fields': (('submission_date', 'last_update_date', ),)
        }),
        ('File', {
            'fields': ('file',)
        })
    )
    filter_horizontal = ()
    list_display = ('title', 'conference', 'submitter', 'submission_date', 'last_update_date')
    list_filter = ('conference__title',)
    ordering = ('conference',)
    readonly_fields = ('submission_date', 'last_update_date', )
    search_fields = ('title', 'conference')


class MembershipInline(admin.TabularInline):
    from django import forms
    from django.db import models

    extra = 0
    exclude = ('last_accessed',)
    formfield_overrides = {
        models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
    }
    model = Membership


class ConferenceAdmin(admin.ModelAdmin):
    inlines = (MembershipInline, )
    fieldsets = (
        ('Conference information', {
            'fields': ('title', 'url', 'domains')
        }),
        ('Date information', {
            'fields': (('start_date',), ('submissions_start_date', 'submissions_end_date'), ('reviews_start_date', 'reviews_end_date'),)
        }),
        ('Special datas', {
            'classes': ('collapse',),
            'fields': ('access_key', 'is_open', 'has_finalize_paper_selections')
        })
    )
    readonly_fields = ('access_key', 'is_open', 'has_finalize_paper_selections')

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs.update({'form': AdminConferenceForm})

        return super(ConferenceAdmin, self).get_form(request, obj, **kwargs)


site = admin.AdminSite()
site.register(User, UserAdmin)
site.register(Conference, ConferenceAdmin)
site.register(Membership)
site.register(Paper, PaperAdmin)

