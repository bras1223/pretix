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
import logging
from datetime import datetime, time, timedelta

from dateutil.tz import datetime_exists
from django.db import models
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.timezone import make_aware, now
from django.utils.translation import gettext_lazy as _, ngettext
from django_scopes import ScopedManager
from i18nfield.fields import I18nCharField, I18nTextField

from pretix.base.email import get_email_context
from pretix.base.i18n import language
from pretix.base.models import (
    Checkin, Event, InvoiceAddress, Item, Order, OrderPosition, SubEvent,
    fields,
)
from pretix.base.models.base import LoggingMixin

logger = logging.getLogger(__name__)


class ScheduledMail(models.Model):
    STATE_SCHEDULED = 'scheduled'
    STATE_FAILED = 'failed'
    STATE_COMPLETED = 'completed'
    STATE_MISSED = 'missed'

    STATE_CHOICES = [
        (STATE_SCHEDULED, _('scheduled')),
        (STATE_FAILED, _('failed')),
        (STATE_COMPLETED, _('completed')),
        (STATE_MISSED, _('missed')),
    ]

    id = models.BigAutoField(primary_key=True)
    rule = models.ForeignKey("Rule", on_delete=models.CASCADE)
    subevent = models.ForeignKey(SubEvent, null=True, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    last_computed = models.DateTimeField(auto_now_add=True)
    computed_datetime = models.DateTimeField(db_index=True)

    state = models.CharField(max_length=100, choices=STATE_CHOICES, default=STATE_SCHEDULED)
    last_successful_order_id = models.BigIntegerField(null=True)

    class Meta:
        unique_together = ('rule', 'subevent'),

    def save(self, **kwargs):
        if not self.computed_datetime:
            self.recompute()
            if 'update_fields' in kwargs:
                kwargs['update_fields'] = {'computed_datetime', 'last_computed', 'state'}.union(kwargs['update_fields'])

        super().save(**kwargs)

    def recompute(self):
        if self.state == self.STATE_COMPLETED:
            return

        if self.rule.date_is_absolute:
            self.computed_datetime = self.rule.send_date
        else:
            e = self.subevent or self.event
            o_days = self.rule.send_offset_days
            if not self.rule.offset_is_after:
                o_days *= -1

            offset = timedelta(days=o_days)
            st = self.rule.send_offset_time
            base_time = (e.date_to or e.date_from) if self.rule.offset_to_event_end else e.date_from
            d = base_time.astimezone(self.event.timezone).date() + offset
            self.computed_datetime = make_aware(
                datetime.combine(d, time(hour=st.hour, minute=st.minute, second=st.second, microsecond=0, fold=1)),
                self.event.timezone,
            )
            if not datetime_exists(self.computed_datetime):
                self.computed_datetime = make_aware(
                    datetime.combine(d, time(hour=st.hour, minute=st.minute, second=st.second, microsecond=0)) + timedelta(hours=1),
                    self.event.timezone,
                )

        if self.computed_datetime > timezone.now() and self.state == self.STATE_MISSED:
            self.state = self.STATE_SCHEDULED
        self.last_computed = timezone.now()

    @property
    def supports_catch_up(self):
        rule = self.rule
        return (
            rule.catch_up_late_orders
            and not rule.date_is_absolute
            and not rule.offset_is_after
            and rule.send_offset_time is not None
        )

    def _event_or_subevent(self):
        return self.subevent or self.event

    def final_catch_up_datetime(self):
        """Last regular send moment: day before the (sub)event at the rule's time of day."""
        if not self.supports_catch_up:
            return None
        e = self._event_or_subevent()
        base_time = (e.date_to or e.date_from) if self.rule.offset_to_event_end else e.date_from
        d = base_time.astimezone(self.event.timezone).date() - timedelta(days=1)
        st = self.rule.send_offset_time
        dt = make_aware(
            datetime.combine(d, time(hour=st.hour, minute=st.minute, second=st.second, microsecond=0, fold=1)),
            self.event.timezone,
        )
        if not datetime_exists(dt):
            dt = make_aware(
                datetime.combine(d, time(hour=st.hour, minute=st.minute, second=st.second, microsecond=0)) + timedelta(hours=1),
                self.event.timezone,
            )
        # Never schedule catch-up after the primary send time would already be the day before
        # (e.g. rule is "1 day before") - primary itself is the final regular moment.
        if self.computed_datetime and dt < self.computed_datetime:
            return self.computed_datetime
        return dt

    def todays_send_datetime(self, when=None):
        when = when or timezone.now()
        st = self.rule.send_offset_time
        local = when.astimezone(self.event.timezone)
        dt = make_aware(
            datetime.combine(local.date(), time(hour=st.hour, minute=st.minute, second=st.second, microsecond=0, fold=1)),
            self.event.timezone,
        )
        if not datetime_exists(dt):
            dt = make_aware(
                datetime.combine(local.date(), time(hour=st.hour, minute=st.minute, second=st.second, microsecond=0)) + timedelta(hours=1),
                self.event.timezone,
            )
        return dt

    def due_for_send(self, when=None):
        """Whether the periodic task should process this scheduled mail now."""
        when = when or timezone.now()
        if when < self.computed_datetime:
            return False
        if not self.supports_catch_up:
            return True
        today_send = self.todays_send_datetime(when)
        final = self.final_catch_up_datetime()
        if when <= final:
            # Evening batch: only at/after the configured time of day
            return when >= today_send
        # After the last regular slot: one more pass for anyone still pending who ordered before final
        return True

    def order_cutoff_for_send(self, when=None):
        when = when or timezone.now()
        if not self.supports_catch_up:
            return None
        final = self.final_catch_up_datetime()
        today_send = self.todays_send_datetime(when)
        if when > final:
            return final
        return min(today_send, final)

    def _status_q(self):
        status_q = Q(status__in=self.rule.restrict_to_status)
        if 'n__pending_approval' in self.rule.restrict_to_status:
            status_q |= Q(status=Order.STATUS_PENDING, require_approval=True)
        if 'n__not_pending_approval_and_not_valid_if_pending' in self.rule.restrict_to_status:
            status_q |= Q(status=Order.STATUS_PENDING, require_approval=False, valid_if_pending=False)
        if 'n__valid_if_pending' in self.rule.restrict_to_status:
            status_q |= Q(status=Order.STATUS_PENDING, require_approval=False, valid_if_pending=True)
        if 'n__pending_overdue' in self.rule.restrict_to_status:
            status_q |= Q(status=Order.STATUS_PENDING, require_approval=False, valid_if_pending=False,
                          expires__lt=now())
        return status_q

    def _order_positions_queryset(self, order=None):
        e = self.event
        op_qs = OrderPosition.objects.filter(
            order__event=self.event,
            canceled=False,
        )
        if order is not None:
            op_qs = op_qs.filter(order=order)

        filter_orders_by_op = False

        if self.subevent_id:
            filter_orders_by_op = True
            op_qs = op_qs.filter(subevent_id=self.subevent_id)
        elif e.has_subevents and (self.rule.date_is_absolute or self.rule.offset_relative_to_subevent):
            if self.rule.subevent_id:
                filter_orders_by_op = True
                op_qs = op_qs.filter(subevent_id=self.rule.subevent_id)
            else:
                self.rule.sync_scheduled_mails()
                raise ValueError("Scheduled mail for event series is missing its subevent assignment")
        elif self.rule.subevent_id:
            filter_orders_by_op = True
            op_qs = op_qs.filter(subevent=self.rule.subevent_id)

        if not self.rule.all_products:
            filter_orders_by_op = True
            limit_products = self.rule.limit_products.values_list('pk', flat=True)
            op_qs = op_qs.filter(item_id__in=limit_products)

        if self.rule.checked_in_status == "no_checkin":
            filter_orders_by_op = True
            op_qs = op_qs.filter(~Exists(Checkin.objects.filter(position_id=OuterRef('pk'), list__consider_tickets_used=True)))
        elif self.rule.checked_in_status == "checked_in":
            filter_orders_by_op = True
            op_qs = op_qs.filter(Exists(Checkin.objects.filter(position_id=OuterRef('pk'), list__consider_tickets_used=True)))

        return op_qs, filter_orders_by_op

    def _send_to_order(self, o, position_ids):
        e = self.event
        send_to_orders = self.rule.send_to in (Rule.CUSTOMERS, Rule.BOTH)
        send_to_attendees = self.rule.send_to in (Rule.ATTENDEES, Rule.BOTH)

        with language(o.locale, e.settings.region):
            positions = list(o.positions.all())
            send_to_order = send_to_orders

            try:
                ia = o.invoice_address
            except InvoiceAddress.DoesNotExist:
                ia = InvoiceAddress(order=o)

            if send_to_attendees:
                parent_op = None
                sent_to_positions = set()
                for p in positions:
                    if p.addon_to_id is None:
                        parent_op = p
                    elif not parent_op or p.addon_to_id != parent_op.id:
                        logger.warning(f"Add-ons are mixed up for position #{p.positionid} in order {o.full_code}")
                        continue

                    if p.id not in position_ids:
                        continue

                    if p.addon_to_id and (
                        not p.attendee_email or p.attendee_email == parent_op.attendee_email
                    ):
                        p = parent_op

                    if p.pk in sent_to_positions:
                        continue

                    if not p.attendee_email or p.attendee_email == o.email:
                        send_to_order = True
                        continue

                    email_ctx = get_email_context(
                        event=e,
                        order=o,
                        invoice_address=ia,
                        position=p,
                        event_or_subevent=self.subevent or e,
                    )
                    p.send_mail(self.rule.subject, self.rule.template, email_ctx,
                                attach_ical=self.rule.attach_ical,
                                log_entry_type='pretix.plugins.sendmail.rule.order.position.email.sent')
                    sent_to_positions.add(p.pk)

            if send_to_order and o.email:
                email_ctx = get_email_context(
                    event=e,
                    order=o,
                    invoice_address=ia,
                    event_or_subevent=self.subevent or e,
                )
                o.send_mail(self.rule.subject, self.rule.template, email_ctx,
                            attach_ical=self.rule.attach_ical,
                            log_entry_type='pretix.plugins.sendmail.rule.order.email.sent')

        self._mark_order_sent(o)

    def _already_sent_q(self, order_field='pk'):
        qs = RuleOrderSent.objects.filter(rule=self.rule, order_id=OuterRef(order_field))
        if self.subevent_id:
            qs = qs.filter(subevent_id=self.subevent_id)
        else:
            qs = qs.filter(subevent__isnull=True)
        return qs

    def _mark_order_sent(self, o):
        qs = RuleOrderSent.objects.filter(rule=self.rule, order=o)
        if self.subevent_id:
            qs = qs.filter(subevent_id=self.subevent_id)
        else:
            qs = qs.filter(subevent__isnull=True)
        if not qs.exists():
            RuleOrderSent.objects.create(rule=self.rule, order=o, subevent=self.subevent)

    def _was_sent_to_order(self, order):
        qs = RuleOrderSent.objects.filter(rule=self.rule, order=order)
        if self.subevent_id:
            return qs.filter(subevent_id=self.subevent_id).exists()
        return qs.filter(subevent__isnull=True).exists()

    def send_to_order_if_eligible(self, order):
        """Send this scheduled mail to a single order if it matches and was not sent yet."""
        if self._was_sent_to_order(order):
            return False
        if order.event_id != self.event_id:
            return False
        if not Order.objects.filter(pk=order.pk).filter(self._status_q()).exists():
            return False

        op_qs, filter_orders_by_op = self._order_positions_queryset(order=order)
        if filter_orders_by_op and not op_qs.exists():
            return False

        position_ids = set(op_qs.values_list('id', flat=True))
        self._send_to_order(order, position_ids)
        return True

    def send(self):
        if self.state not in (ScheduledMail.STATE_SCHEDULED, ScheduledMail.STATE_FAILED):
            raise ValueError("Should not be called in this state")

        e = self.event
        op_qs, filter_orders_by_op = self._order_positions_queryset()
        status_q = self._status_q()

        orders = e.orders.all()
        if self.last_successful_order_id:
            orders = orders.filter(pk__gt=self.last_successful_order_id)

        orders = orders.annotate(
            _sendmail_already_sent=Exists(self._already_sent_q())
        ).filter(_sendmail_already_sent=False)

        cutoff = self.order_cutoff_for_send()
        if cutoff is not None:
            orders = orders.filter(datetime__lte=cutoff)

        if filter_orders_by_op:
            orders = orders.filter(pk__in=op_qs.values_list('order_id', flat=True))
        orders = orders.filter(
            status_q,
        ).order_by('pk').select_related('invoice_address').prefetch_related('positions')

        position_ids = set(op_qs.values_list('id', flat=True))

        for o in orders:
            self._send_to_order(o, position_ids)
            self.last_successful_order_id = o.pk


class Rule(models.Model, LoggingMixin):
    CUSTOMERS = "orders"
    ATTENDEES = "attendees"
    BOTH = "both"

    SEND_TO_CHOICES = [
        (CUSTOMERS, _("Everyone who created a ticket order")),
        (ATTENDEES, _("Every attendee (falling back to the order contact when no attendee email address is given)")),
        (BOTH, _('Both (all order contact addresses and all attendee email addresses)'))
    ]

    CHECK_IN_STATUS_CHOICES = [
        (None, _("Everyone")),
        ("checked_in", _("Anyone who is or was checked in")),
        ("no_checkin", _("Anyone who never checked in before"))
    ]

    id = models.BigAutoField(primary_key=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sendmail_rules')
    subevent = models.ForeignKey(SubEvent, null=True, on_delete=models.PROTECT)

    subject = I18nCharField(max_length=255, verbose_name=_('Subject'))
    template = I18nTextField(verbose_name=_('Message'))

    all_products = models.BooleanField(default=True, verbose_name=_('All products'))
    limit_products = models.ManyToManyField(Item, blank=True, verbose_name=_('Limit products'))

    restrict_to_status = fields.MultiStringField(
        verbose_name=_("Restrict to orders with status"),
        default=['p', 'n__valid_if_pending'],
    )

    checked_in_status = models.CharField(
        verbose_name=_("Restrict to check-in status"),
        default=None,
        choices=CHECK_IN_STATUS_CHOICES,
        max_length=10,
        null=True,
        blank=True,
    )

    attach_ical = models.BooleanField(
        default=False,
        verbose_name=_("Attach calendar files"),
    )

    # either send_date or send_offset_* have to be set
    send_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Send date'))
    send_offset_days = models.IntegerField(null=True, blank=True, verbose_name=_('Number of days'))
    send_offset_time = models.TimeField(null=True, blank=True, verbose_name=_('Time of day'))

    date_is_absolute = models.BooleanField(default=True, blank=True)
    offset_to_event_end = models.BooleanField(default=False, blank=True)  # no verbose name because not actually
    offset_is_after = models.BooleanField(default=False, blank=True)  # displayed in any forms
    offset_relative_to_subevent = models.BooleanField(
        default=True,
        verbose_name=_('Schedule relative to individual event dates'),
        help_text=_(
            'If enabled, a separate email is scheduled for each event date based on that date. '
            'If disabled, one email is scheduled relative to the main event date.'
        ),
    )

    send_to = models.CharField(max_length=10, choices=SEND_TO_CHOICES, default=CUSTOMERS, verbose_name=_('Send email to'))

    enabled = models.BooleanField(
        default=True,
        verbose_name=_('Enabled'),
        help_text=_('Only enabled rules are actually sent')
    )

    catch_up_late_orders = models.BooleanField(
        default=False,
        verbose_name=_('Catch up late orders'),
        help_text=_(
            'If someone orders after the scheduled send time, still send this email at the configured time of day '
            'on later days, until the day before the event. Orders placed after that last moment receive the email '
            'immediately.'
        ),
    )

    objects = ScopedManager(organizer='event__organizer')

    def uses_per_subevent_scheduled_mails(self):
        if not self.event.has_subevents or self.subevent_id:
            return False
        if self.date_is_absolute:
            return True
        return self.offset_relative_to_subevent

    def sync_scheduled_mails(self, *, is_creation=False):
        keep_states = [ScheduledMail.STATE_COMPLETED]
        create_sms = []

        if self.event.has_subevents:
            if self.subevent_id:
                sm, created = ScheduledMail.objects.get_or_create(
                    rule=self, subevent_id=self.subevent_id, event=self.event,
                )
                if created or not sm.computed_datetime:
                    sm.recompute()
                    sm.save(update_fields=['computed_datetime', 'last_computed', 'state'])
            elif not self.date_is_absolute and not self.offset_relative_to_subevent:
                sm, created = ScheduledMail.objects.get_or_create(
                    rule=self, subevent=None, event=self.event,
                )
                if created or not sm.computed_datetime:
                    sm.recompute()
                    sm.save(update_fields=['computed_datetime', 'last_computed', 'state'])
            else:
                for se in self.event.subevents.annotate(has_sm=Exists(ScheduledMail.objects.filter(
                        subevent=OuterRef('pk'), rule=self))).filter(has_sm=False):
                    sm = ScheduledMail(rule=self, subevent=se, event=self.event)
                    sm.recompute()
                    create_sms.append(sm)
                if create_sms:
                    ScheduledMail.objects.bulk_create(create_sms)
        else:
            sm, created = ScheduledMail.objects.get_or_create(
                rule=self, subevent=None, event=self.event,
            )
            if created or not sm.computed_datetime:
                sm.recompute()
                sm.save(update_fields=['computed_datetime', 'last_computed', 'state'])

        if not is_creation:
            if self.event.has_subevents:
                if self.subevent_id:
                    ScheduledMail.objects.filter(
                        Q(rule=self),
                        ~Q(subevent_id=self.subevent_id),
                        ~Q(state__in=keep_states)
                    ).delete()
                elif not self.date_is_absolute and not self.offset_relative_to_subevent:
                    ScheduledMail.objects.filter(
                        Q(rule=self),
                        Q(subevent__isnull=False),
                        ~Q(state__in=keep_states)
                    ).delete()
                else:
                    ScheduledMail.objects.filter(
                        Q(rule=self),
                        Q(subevent__isnull=True),
                        ~Q(state__in=keep_states)
                    ).delete()

            update_sms = []
            for sm in self.scheduledmail_set.prefetch_related('event').select_related('subevent'):
                if sm in create_sms:
                    continue
                previous = sm.computed_datetime
                sm.recompute()
                if sm.computed_datetime != previous:
                    update_sms.append(sm)

            ScheduledMail.objects.bulk_update(update_sms, ['computed_datetime', 'last_computed', 'state'], 100)

    def save(self, **kwargs):
        is_creation = not self.pk
        super().save(**kwargs)
        self.sync_scheduled_mails(is_creation=is_creation)

    @property
    def human_readable_time(self):
        if self.date_is_absolute:
            d = self.send_date.astimezone(self.event.timezone)
            return _('on {date} at {time}').format(date=date_format(d, 'SHORT_DATE_FORMAT'),
                                                   time=date_format(d, 'TIME_FORMAT'))

        per_date = (
            self.event.has_subevents
            and self.offset_relative_to_subevent
            and not self.subevent
        )
        if self.offset_to_event_end:
            if self.offset_is_after:
                if per_date:
                    s = ngettext(
                        '%(count)d day after event date end at %(time)s',
                        '%(count)d days after event date end at %(time)s',
                        self.send_offset_days
                    )
                else:
                    s = ngettext(
                        '%(count)d day after event end at %(time)s',
                        '%(count)d days after event end at %(time)s',
                        self.send_offset_days
                    )
            else:
                if per_date:
                    s = ngettext(
                        '%(count)d day before event date end at %(time)s',
                        '%(count)d days before event date end at %(time)s',
                        self.send_offset_days
                    )
                else:
                    s = ngettext(
                        '%(count)d day before event end at %(time)s',
                        '%(count)d days before event end at %(time)s',
                        self.send_offset_days
                    )
        elif self.offset_is_after:
            if per_date:
                s = ngettext(
                    '%(count)d day after event date start at %(time)s',
                    '%(count)d days after event date start at %(time)s',
                    self.send_offset_days
                )
            else:
                s = ngettext(
                    '%(count)d day after event start at %(time)s',
                    '%(count)d days after event start at %(time)s',
                    self.send_offset_days
                )
        else:
            if per_date:
                s = ngettext(
                    '%(count)d day before event date start at %(time)s',
                    '%(count)d days before event date start at %(time)s',
                    self.send_offset_days
                )
            else:
                s = ngettext(
                    '%(count)d day before event start at %(time)s',
                    '%(count)d days before event start at %(time)s',
                    self.send_offset_days
                )
        return s % {
            'count': self.send_offset_days,
            'time': date_format(self.send_offset_time, 'TIME_FORMAT')
        }


class RuleOrderSent(models.Model):
    """Tracks that a scheduled rule email was already sent for an order (and optional subevent)."""

    id = models.BigAutoField(primary_key=True)
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name='orders_sent')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='sendmail_rules_sent')
    subevent = models.ForeignKey(SubEvent, null=True, blank=True, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('rule', 'order', 'subevent'),)
