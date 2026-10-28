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
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import re_path
from django_scopes import scopes_disabled

from pretix.base.models import CheckinList, User

from .views import IndexView


def token_login_redirect(request, token):
    try:
        if not token:
            return HttpResponse("Token is required.", status=400)

        user = User.objects.get(auth_token=token)

        with scopes_disabled():
            checkin_list = None
            if user.checkinlist_id not in (None, ''):
                try:
                    checkin_list = CheckinList.objects.select_related(
                        'event', 'event__organizer'
                    ).get(pk=int(user.checkinlist_id))
                except (ValueError, TypeError, CheckinList.DoesNotExist):
                    checkin_list = None

        if not checkin_list:
            return HttpResponse("No check-in list configured for this user.", status=403)

        auth_logout(request)
        auth_login(request, user)
        return redirect(
            f'/control/event/{checkin_list.event.organizer.slug}/'
            f'{checkin_list.event.slug}/wwpcheckin/#{checkin_list.pk}'
        )
    except User.DoesNotExist:
        return HttpResponse("Invalid token.", status=401)


urlpatterns = [
    re_path(r'^wwp/(?P<token>[a-zA-Z0-9\-]+)/$',
            token_login_redirect, name='token_login'),
    re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/wwpcheckin/$',
            IndexView.as_view(), name='index'),
]
