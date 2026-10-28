const body = document.body

export const timezone = body.dataset.timezone ?? 'UTC'
export const datetimeFormat = body.dataset.datetimeformat ?? 'L LT'
export const dateFormat = body.dataset.dateformat ?? 'L'
export const timeFormat = body.dataset.timeformat ?? 'LT'
export const datetimeLocale = body.dataset.datetimelocale ?? 'en'
export const pretixLocale = body.dataset.pretixlocale ?? 'en'

moment.locale(datetimeLocale)

const NL: Record<string, string> = {
	'Select a check-in list': 'Selecteer een check-in-lijst',
	'No active check-in lists found.': 'Geen actieve check-in-lijsten gevonden.',
	'Switch check-in list': 'Andere check-in-lijst kiezen',
	'Search results': 'Zoekresultaten',
	'No tickets found': 'Geen tickets gevonden',
	'Tickets in this order': 'Tickets in deze bestelling',
	'Check in all tickets': 'Alle tickets inchecken',
	'Check out all tickets': 'Alle tickets uitchecken',
	'Checking in tickets…': 'Tickets inchecken…',
	'Done': 'Klaar',
	'tickets remaining': 'tickets resterend',
	'Upselling': 'Meerverkoop',
	'Add-ons': 'Add-ons',
	'Check in these tickets': 'Deze tickets inchecken',
	'Result': 'Resultaat',
	'This ticket requires special attention': 'Dit ticket heeft speciale aandacht nodig',
	'Switch direction': 'Richting veranderen',
	'Entry': 'Binnenkomst',
	'Exit': 'Vertrek',
	'Scan or enter a ticket code…': 'Scan of voer een ticketcode in…',
	'Unknown ticket code': 'Onbekende ticketcode',
	'Open QR scanner': 'QR-scanner openen',
	'Close QR scanner': 'QR-scanner sluiten',
	'Load more': 'Meer laden',
	'Valid': 'Geldig',
	'Unpaid': 'Niet betaald',
	'Canceled': 'Geannuleerd',
	'Confirmed': 'Bevestigd',
	'Approval pending': 'Goedkeuring in behandeling',
	'Redeemed': 'Ingewisseld',
	'Cancel': 'Annuleren',
	'Continue': 'Doorgaan',
	'Ticket not paid': 'Ticket niet betaald',
	'This ticket is not yet paid. Do you want to continue anyways?': 'Dit ticket is nog niet betaald. Wilt u toch doorgaan?',
	'Additional information required': 'Extra informatie vereist',
	'Valid ticket': 'Geldig ticket',
	'Exit recorded': 'Vertrek opgeslagen',
	'Ticket already used': 'Ticket al gebruikt',
	'Information required': 'Informatie nodig',
	'Unknown ticket': 'Onbekend ticket',
	'Ticket type not allowed here': 'Tickettype hier niet toegestaan',
	'Entry not allowed': 'Binnenkomst niet toegestaan',
	'Ticket code revoked/changed': 'Ticketcode ingetrokken/veranderd',
	'Ticket blocked': 'Ticket geblokkeerd',
	'Ticket not valid at this time': 'Ticket is op dit moment niet geldig',
	'Order canceled': 'Bestelling geannuleerd',
	'Ticket code is ambiguous on list': 'Ticketcode op de lijst is niet eenduidig',
	'Order not approved': 'Bestelling niet goedgekeurd',
	'Checked-in Tickets': 'Ingecheckte tickets',
	'Valid Tickets': 'Geldige tickets',
	'Currently inside': 'Nu binnen',
	'Yes': 'Ja',
	'No': 'Nee',
	'WWP Check-in': 'WWP Check-in',
	'Extras': 'Extra\'s',
}

function isDutch (): boolean {
	return pretixLocale.toLowerCase().startsWith('nl')
}

export function gettext (msgid: string): string {
	if (isDutch() && NL[msgid]) {
		return NL[msgid]
	}
	if (typeof django !== 'undefined' && typeof django.gettext !== 'undefined') {
		return django.gettext(msgid)
	}
	return msgid
}

export function ngettext (singular: string, plural: string, count: number): string {
	if (typeof django !== 'undefined' && typeof django.ngettext !== 'undefined') {
		return django.ngettext(singular, plural, count)
	}
	return plural
}

export type I18nString = string | Record<string, string> | null | undefined

export function i18nstringLocalize (obj: I18nString): string {
	// external
	return i18nstring_localize(obj)
}

export const STRINGS: Record<string, string> = {
	'checkinlist.select': gettext('Select a check-in list'),
	'checkinlist.none': gettext('No active check-in lists found.'),
	'checkinlist.switch': gettext('Switch check-in list'),
	'results.headline': gettext('Search results'),
	'results.none': gettext('No tickets found'),
	'order.headline': gettext('Tickets in this order'),
	'order.check_all': gettext('Check in all tickets'),
	'order.check_all_exit': gettext('Check out all tickets'),
	'order.checking_all': gettext('Checking in tickets…'),
	'order.done': gettext('Done'),
	'order.remaining': gettext('tickets remaining'),
	'order.upselling': gettext('Upselling'),
	'order.addons': gettext('Add-ons'),
	'order.qty': '×',
	'order.check_group': gettext('Check in these tickets'),
	'order.extras': gettext('Extras'),
	'check.headline': gettext('Result'),
	'check.attention': gettext('This ticket requires special attention'),
	'scantype.switch': gettext('Switch direction'),
	'scantype.entry': gettext('Entry'),
	'scantype.exit': gettext('Exit'),
	'input.placeholder': gettext('Scan or enter a ticket code…'),
	'input.invalid': gettext('Unknown ticket code'),
	'scanner.show': gettext('Open QR scanner'),
	'scanner.hide': gettext('Close QR scanner'),
	'wwp.badge': gettext('WWP Check-in'),
	'pagination.next': gettext('Load more'),
	'status.p': gettext('Valid'),
	'status.n': gettext('Unpaid'),
	'status.c': gettext('Canceled'),
	'status.e': gettext('Canceled'),
	'status.pending_valid': gettext('Confirmed'),
	'status.require_approval': gettext('Approval pending'),
	'status.redeemed': gettext('Redeemed'),
	'modal.cancel': gettext('Cancel'),
	'modal.continue': gettext('Continue'),
	'modal.unpaid.head': gettext('Ticket not paid'),
	'modal.unpaid.text': gettext('This ticket is not yet paid. Do you want to continue anyways?'),
	'modal.questions': gettext('Additional information required'),
	'result.ok': gettext('Valid ticket'),
	'result.exit': gettext('Exit recorded'),
	'result.already_redeemed': gettext('Ticket already used'),
	'result.questions': gettext('Information required'),
	'result.invalid': gettext('Unknown ticket'),
	'result.product': gettext('Ticket type not allowed here'),
	'result.unpaid': gettext('Ticket not paid'),
	'result.rules': gettext('Entry not allowed'),
	'result.revoked': gettext('Ticket code revoked/changed'),
	'result.blocked': gettext('Ticket blocked'),
	'result.invalid_time': gettext('Ticket not valid at this time'),
	'result.canceled': gettext('Order canceled'),
	'result.ambiguous': gettext('Ticket code is ambiguous on list'),
	'result.unapproved': gettext('Order not approved'),
	'status.checkin': gettext('Checked-in Tickets'),
	'status.position': gettext('Valid Tickets'),
	'status.inside': gettext('Currently inside'),
	yes: gettext('Yes'),
	no: gettext('No'),
}

export interface SubEvent {
	name: Record<string, string>
	date_from: string
}

export function formatSubevent (subevent: SubEvent | null | undefined): string {
	if (!subevent) return ''
	const name = i18nstringLocalize(subevent.name)
	const date = moment.utc(subevent.date_from).tz(timezone).format(datetimeFormat)
	return `${name} · ${date}`
}

export interface Question {
	type: string
}

export function formatAnswer (value: string, question: Question): string {
	if (question.type === 'B' && value === 'True') {
		return STRINGS['yes']
	} else if (question.type === 'B' && value === 'False') {
		return STRINGS['no']
	} else if (question.type === 'W' && value) {
		return moment(value).tz(timezone).format('L LT')
	} else if (question.type === 'D' && value) {
		return moment(value).format('L')
	}
	return value
}
