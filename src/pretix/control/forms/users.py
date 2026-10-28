#
# This file is part of pretix (Community Edition).
#
# Copyright (C) 2014-2020  Raphael Michel and contributors
# Copyright (C) 2020-today pretix GmbH and contributors
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General
# Public License as published by the Free Software Foundation in version 3 of the License.
#
# ADDITIONAL TERMS APPLY: Pursuant to Section 7 of the GNU Affero General Public License, additional terms are
# applicable granting you additional permissions and placing additional restrictions on your usage of this software.
# Please refer to the pretix LICENSE file to obtain the full terms applicable to this work. If you did not receive
# this file, see <https://pretix.eu/about/en/license>.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License along with this program.  If not, see
# <https://www.gnu.org/licenses/>.
#
from django import forms
from django.contrib import messages
from django.contrib.auth.password_validation import (
    password_validators_help_texts, validate_password,
)
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_scopes import scopes_disabled
from pytz import common_timezones

from pretix.base.models import CheckinList, Event, User
from pretix.base.models.auth import StaffSession


class StaffSessionForm(forms.ModelForm):
    class Meta:
        model = StaffSession
        fields = ['comment']


class UserEditForm(forms.ModelForm):
    error_messages = {
        'duplicate_identifier': _("There already is an account associated with this email address. "
                                  "Please choose a different one."),
        'pw_mismatch': _("Please enter the same password twice"),
        'list_event_mismatch': _("Please select a check-in list that belongs to the selected event."),
    }

    new_pw = forms.CharField(max_length=255,
                             required=False,
                             label=_("New password"),
                             widget=forms.PasswordInput())
    new_pw_repeat = forms.CharField(max_length=255,
                                    required=False,
                                    label=_("Repeat new password"),
                                    widget=forms.PasswordInput())
    timezone = forms.ChoiceField(
        choices=((a, a) for a in common_timezones),
        label=_("Default timezone"),
        help_text=_('Only used for views that are not bound to an event. For all '
                    'event views, the event timezone is used instead.')
    )
    checkin_event = forms.ModelChoiceField(
        label=_("Check-in event"),
        queryset=Event.objects.none(),
        required=False,
        empty_label=_("---------"),
        help_text=_("Event used when logging in via a check-in auth token."),
    )
    checkin_list = forms.ModelChoiceField(
        label=_("Check-in list"),
        queryset=CheckinList.objects.none(),
        required=False,
        empty_label=_("---------"),
        help_text=_("Check-in list opened after token login."),
    )

    class Meta:
        model = User
        fields = [
            'fullname',
            'locale',
            'timezone',
            'email',
            'auth_token',
            'require_2fa',
            'is_active',
            'is_verified',
            'is_staff',
            'needs_password_change',
            'last_login'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['last_login'].disabled = True
        self.fields['checkin_event'].widget.attrs['data-checkinlists-url'] = reverse(
            'control:users.checkinlists'
        )
        if self.instance and self.instance.auth_backend != 'native':
            del self.fields['new_pw']
            del self.fields['new_pw_repeat']
            self.fields['email'].disabled = True

        with scopes_disabled():
            events = Event.objects.select_related('organizer').order_by('organizer__name', 'name')
            self.fields['checkin_event'].queryset = events
            self.fields['checkin_event'].label_from_instance = (
                lambda e: f'{e.organizer.name} / {e.name}'
            )
            self.fields['checkin_list'].label_from_instance = (
                lambda cl: cl.name
            )

            selected_list = None
            raw_list_id = getattr(self.instance, 'checkinlist_id', None)
            if raw_list_id not in (None, ''):
                try:
                    selected_list = CheckinList.objects.select_related('event').get(pk=int(raw_list_id))
                except (ValueError, TypeError, CheckinList.DoesNotExist):
                    selected_list = None

            selected_event_id = None
            if self.is_bound and self.data.get('checkin_event'):
                try:
                    selected_event_id = int(self.data.get('checkin_event'))
                except (TypeError, ValueError):
                    selected_event_id = None
            elif selected_list:
                selected_event_id = selected_list.event_id
                if not self.is_bound:
                    self.fields['checkin_event'].initial = selected_list.event_id
                    self.fields['checkin_list'].initial = selected_list.pk

            if selected_event_id:
                self.fields['checkin_list'].queryset = CheckinList.objects.filter(
                    event_id=selected_event_id
                ).order_by('name')
            else:
                self.fields['checkin_list'].queryset = CheckinList.objects.none()

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(Q(email__iexact=email) & ~Q(pk=self.instance.pk)).exists():
            raise forms.ValidationError(
                self.error_messages['duplicate_identifier'],
                code='duplicate_identifier',
            )
        return email

    def clean_new_pw(self):
        password1 = self.cleaned_data.get('new_pw', '')
        if password1 and validate_password(password1, user=self.instance) is not None:
            raise forms.ValidationError(
                _(password_validators_help_texts()),
                code='pw_invalid'
            )
        return password1

    def clean_new_pw_repeat(self):
        password1 = self.cleaned_data.get('new_pw')
        password2 = self.cleaned_data.get('new_pw_repeat')
        if password1 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['pw_mismatch'],
                code='pw_mismatch'
            )

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('new_pw')

        if password1:
            self.instance.set_password(password1)

        event = cleaned.get('checkin_event')
        checkin_list = cleaned.get('checkin_list')

        if checkin_list and event and checkin_list.event_id != event.pk:
            self.add_error('checkin_list', forms.ValidationError(
                self.error_messages['list_event_mismatch'],
                code='list_event_mismatch',
            ))
        elif checkin_list and not event:
            cleaned['checkin_event'] = checkin_list.event

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        checkin_list = self.cleaned_data.get('checkin_list')
        user.checkinlist_id = str(checkin_list.pk) if checkin_list else None
        if commit:
            user.save()
            self.save_m2m()
        return user

    def form_invalid(self, form):
        messages.error(self.request, _('Your changes could not be saved. See below for details.'))
        return super().form_invalid(form)
