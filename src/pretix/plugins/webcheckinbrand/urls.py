#
# This file is part of pretix (Community Edition).
#
# Copyright (C) 2014-2020 Raphael Michel and contributors
# Copyright (C) 2020-2021 rami.io GmbH and contributors
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
from django.urls import re_path
from pretix.base.models import User
from django.contrib.auth import (
    authenticate, login as auth_login, logout as auth_logout,
)
from django.shortcuts import redirect, render
from django.http import HttpResponse

from .views import IndexView
def token_login_redirect(request, token):
    try:
        if not token:
            return HttpResponse(json.dumps({"error": "Token is required."}), status=400, content_type="application/json")

        user = User.objects.get(auth_token=token)
        auth_login(request, user)
        return redirect(f'/control/event/weerter-brandslang/digitaal/webcheckin-brand/#{user.checkinlist_id}')
    except User.DoesNotExist:
        return HttpResponse("Invalid token.", status=401)


urlpatterns = [
    re_path(r'^brand/(?P<token>[a-zA-Z0-9\-]+)/$',
            token_login_redirect, name='index'),
    re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/webcheckin-brand/$',
            IndexView.as_view(), name='index'),
]
