<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { api } from '../api'
import type { CheckinList, ItemCategory, Position, RedeemResponse, AnswerQuestion } from '../api'
import { STRINGS, i18nstringLocalize, formatSubevent, formatAnswer } from '../i18n'
import { groupOrderTickets } from '../orderGroups'

import CheckinlistSelect from './checkinlist-select.vue'
import OrderTicketGroup from './order-ticket-group.vue'
import Datefield from './datefield.vue'
import Timefield from './timefield.vue'
import Datetimefield from './datetimefield.vue'
import Qrscanner from './qrscanner.vue'

const props = defineProps<{
	eventName?: string
}>()

const COUNTRIES = JSON.parse(document.querySelector('#countries')?.textContent ?? '[]')

const answers = ref<Record<string, string>>({})

// Checkin list selection
const checkinlist = ref<CheckinList | null>(null)

function selectList (list: CheckinList) {
	checkinlist.value = list
	location.hash = '#' + list.id
	refocus()
	ensureCategories()
}

const categories = ref<ItemCategory[]>([])
let categoriesLoaded = false

async function ensureCategories () {
	if (categoriesLoaded) return
	try {
		const data = await api.fetchCategories()
		categories.value = data.results || []
		categoriesLoaded = true
	} catch {
		categories.value = []
	}
}

// QR scanner (shown only after button click)
const showScanner = ref(false)

function toggleScanner () {
	showScanner.value = !showScanner.value
}

// WWP check-in is entry-only
const type = ref<'entry'>('entry')

// Input/query
const inputEl = ref<HTMLInputElement>()
const query = ref('')

function refocus () {
	nextTick(() => {
		inputEl.value?.focus()
	})
}

function inputKeyup (e: KeyboardEvent) {
	if (e.key === 'Enter') {
		lookupTicket()
	} else if (query.value === '') {
		clear()
	}
}

function globalKeydown (e: KeyboardEvent | Event) {
	if (!(e instanceof KeyboardEvent)) {
		refocus()
		return
	}

	if (document.activeElement?.classList.contains('searchresult')) {
		if (e.key === 'ArrowDown') {
			(document.activeElement.nextElementSibling as HTMLElement)?.focus()
			e.preventDefault()
			return
		}
		if (e.key === 'ArrowUp') {
			(document.activeElement.previousElementSibling as HTMLElement)?.focus()
			e.preventDefault()
			return
		}
	}

	const nodeName = document.activeElement?.nodeName?.toLowerCase()
	if (nodeName !== 'input' && nodeName !== 'textarea') {
		if (e.key?.match(/^[a-z0-9A-Z+/=<>#]$/)) {
			query.value = ''
			refocus()
		}
	}
}

// Check/redeem
const checkLoading = ref(false)
const checkError = ref<string | null>(null)
const checkResult = ref<RedeemResponse | null>(null)

const checkResultAddons = computed(() => {
	if (!checkResult.value?.position?.addons) return ''
	return checkResult.value.position.addons.map((addon) => {
		if (addon.variation) {
			return `+ ${addon.item.internal_name || i18nstringLocalize(addon.item.name)} – ${i18nstringLocalize(addon.variation.value)}`
		}
		return '+ ' + (addon.item.internal_name || i18nstringLocalize(addon.item.name))
	}).join('\n')
})

const checkResultSubevent = computed(() => formatSubevent(checkResult.value?.position?.subevent))

const checkResultItemvar = computed(() => {
	if (!checkResult.value?.position) return ''
	if (checkResult.value.position.variation) {
		return `${i18nstringLocalize(checkResult.value.position.item.name)} – ${i18nstringLocalize(checkResult.value.position.variation.value)}`
	}
	return i18nstringLocalize(checkResult.value.position.item.name)
})

const checkResultText = computed(() => {
	if (!checkResult.value) return ''
	if (checkResult.value.status === 'ok') {
		return STRINGS['result.ok']
	} else if (checkResult.value.status === 'incomplete') {
		return STRINGS['result.questions']
	} else if (checkResult.value.reason && STRINGS['result.' + checkResult.value.reason]) {
		return STRINGS['result.' + checkResult.value.reason]
	}
	return checkResult.value.reason ?? ''
})

const checkResultColor = computed(() => {
	if (!checkResult.value) return ''
	if (checkResult.value.status === 'ok') return 'green'
	if (checkResult.value.status === 'incomplete') return 'purple'
	if (checkResult.value.reason === 'already_redeemed') return 'orange'
	return 'red'
})

// Modals
const showUnpaidModal = ref(false)
const showQuestionsModal = ref(false)
const questionsModalEl = ref<HTMLFormElement>()

function answerSetM (qid: string, opid: string, checked: boolean) {
	let arr = answers.value[qid] ? answers.value[qid].split(',') : []
	if (checked && !arr.includes(opid)) {
		arr.push(opid)
	} else if (!checked) {
		arr = arr.filter(o => opid !== o)
	}
	answers.value[qid] = arr.join(',')
}

// Ticket lookup (codes only — no free-text search)
const lookupLoading = ref(false)
const lookupError = ref<string | null>(null)

// Order tickets (WWP feature)
const orderTickets = ref<Position[] | null>(null)
const orderCode = ref<string | null>(null)
const orderLoading = ref(false)
const checkAllLoading = ref(false)
const pendingCheckSecret = ref<string | null>(null)

const uncheckedOrderTickets = computed(() => {
	if (!orderTickets.value) return []
	return orderTickets.value.filter(p => !p.checkins?.length)
})

const groupedOrder = computed(() => {
	if (!orderTickets.value?.length) {
		return { ticketGroups: [], upsellCategories: [] }
	}
	return groupOrderTickets(orderTickets.value, categories.value)
})

function handleQRScan (decodedText: string) {
	query.value = decodedText
	lookupTicket()
}

async function loadOrderTickets (code: string) {
	orderLoading.value = true
	orderTickets.value = null
	orderCode.value = code
	checkResult.value = null
	lookupError.value = null

	try {
		await ensureCategories()
		const data = await api.searchOrderPositions(checkinlist.value!.id, code)
		orderLoading.value = false
		if (data.results) {
			orderTickets.value = data.results
		} else {
			lookupError.value = STRINGS['input.invalid']
			orderTickets.value = []
		}
		nextTick(() => {
			inputEl.value?.blur()
		})
	} catch (e) {
		orderLoading.value = false
		orderTickets.value = []
		lookupError.value = String(e)
	}
}

async function refreshOrderTickets () {
	if (!orderCode.value || !checkinlist.value) return
	try {
		const data = await api.searchOrderPositions(checkinlist.value.id, orderCode.value)
		if (data.results) {
			orderTickets.value = data.results
		}
	} catch {
		// keep existing list on refresh failure
	}
}

function closeOrderIfFullyCheckedIn () {
	if (!orderTickets.value?.length) return
	const remaining = orderTickets.value.filter(p => !p.checkins?.length)
	if (!remaining.length) {
		clear()
	}
}

async function lookupTicket () {
	const ticketCode = query.value.trim()
	if (!ticketCode) return

	checkResult.value = null
	orderTickets.value = null
	orderCode.value = null
	lookupLoading.value = true
	lookupError.value = null
	answers.value = {}

	try {
		const data = await api.searchPositions(checkinlist.value!.id, ticketCode)
		lookupLoading.value = false
		query.value = ''

		const exact = data.results?.find(p => p.secret === ticketCode)
		if (exact) {
			await loadOrderTickets(exact.order)
			return
		}

		lookupError.value = STRINGS['input.invalid']
		nextTick(() => {
			inputEl.value?.blur()
		})
	} catch (e) {
		lookupLoading.value = false
		query.value = ''
		lookupError.value = String(e)
	}
}

async function check (
	id: string,
	ignoreUnpaid: boolean,
	keepAnswers: boolean,
	fallbackToSearch: boolean,
	untrusted: boolean
) {
	if (!keepAnswers) {
		answers.value = {}
	} else if (showQuestionsModal.value) {
		if (!questionsModalEl.value?.reportValidity()) return
	}

	pendingCheckSecret.value = id
	showUnpaidModal.value = false
	showQuestionsModal.value = false
	checkLoading.value = true
	checkError.value = null
	checkResult.value = {} as RedeemResponse

	nextTick(() => {
		inputEl.value?.blur()
	})

	try {
		const data = await api.redeemPosition(
			checkinlist.value!.id,
			id,
			{
				questions_supported: true,
				canceled_supported: true,
				ignore_unpaid: ignoreUnpaid,
				type: type.value,
				answers: answers.value,
			},
			untrusted
		)

		checkLoading.value = false
		checkResult.value = data

		if (checkinlist.value?.include_pending && data.status === 'error' && data.reason === 'unpaid') {
			showUnpaidModal.value = true
			nextTick(() => {
				document.querySelector<HTMLButtonElement>('.modal-unpaid .btn-primary')?.focus()
			})
		} else if (data.status === 'incomplete' && data.questions) {
			showQuestionsModal.value = true
			for (const q of data.questions) {
				if (!answers.value[q.id.toString()]) {
					answers.value[q.id.toString()] = ''
				}
				;(q as AnswerQuestion).question = i18nstringLocalize(q.question)
				for (const o of q.options) {
					;(o as { answer: string }).answer = i18nstringLocalize(o.answer)
				}
			}
			nextTick(() => {
				document.querySelector<HTMLElement>('.modal-questions input, .modal-questions select, .modal-questions textarea')?.focus()
			})
		} else if (data.status === 'error' && data.reason === 'invalid' && fallbackToSearch) {
			lookupError.value = STRINGS['input.invalid']
		} else {
			await refreshOrderTickets()
			closeOrderIfFullyCheckedIn()
		}
	} catch (e) {
		checkLoading.value = false
		checkResult.value = {} as RedeemResponse
		checkError.value = String(e)
	}
}

async function checkGroup (positions: Position[]) {
	await checkAll(positions)
}

async function checkAll (positions?: Position[]) {
	const tickets = positions ?? uncheckedOrderTickets.value
	if (!tickets.length || !checkinlist.value) return

	checkAllLoading.value = true
	checkError.value = null
	checkResult.value = null

	let lastResult: RedeemResponse | null = null

	for (const position of tickets) {
		try {
			const data = await api.redeemPosition(
				checkinlist.value.id,
				position.secret,
				{
					questions_supported: true,
					canceled_supported: true,
					ignore_unpaid: false,
					type: type.value,
					answers: {},
				},
				false
			)
			lastResult = data

			if (data.status === 'incomplete' && data.questions) {
				// Stop and let the user answer questions for this ticket
				checkAllLoading.value = false
				checkResult.value = data
				pendingCheckSecret.value = position.secret
				showQuestionsModal.value = true
				for (const q of data.questions) {
					if (!answers.value[q.id.toString()]) {
						answers.value[q.id.toString()] = ''
					}
					;(q as AnswerQuestion).question = i18nstringLocalize(q.question)
					for (const o of q.options) {
						;(o as { answer: string }).answer = i18nstringLocalize(o.answer)
					}
				}
				await refreshOrderTickets()
				return
			}

			if (checkinlist.value.include_pending && data.status === 'error' && data.reason === 'unpaid') {
				checkAllLoading.value = false
				checkResult.value = data
				pendingCheckSecret.value = position.secret
				showUnpaidModal.value = true
				await refreshOrderTickets()
				return
			}
		} catch (e) {
			checkAllLoading.value = false
			checkError.value = String(e)
			await refreshOrderTickets()
			return
		}
	}

	checkAllLoading.value = false
	checkResult.value = lastResult
	await refreshOrderTickets()
	closeOrderIfFullyCheckedIn()
}

function clear () {
	query.value = ''
	lookupLoading.value = false
	lookupError.value = null
	checkLoading.value = false
	checkError.value = null
	checkResult.value = null
	showUnpaidModal.value = false
	showQuestionsModal.value = false
	answers.value = {}
	orderTickets.value = null
	orderCode.value = null
	orderLoading.value = false
	checkAllLoading.value = false
	pendingCheckSecret.value = null
}

onMounted(() => {
	window.addEventListener('focus', globalKeydown)
	document.addEventListener('visibilitychange', globalKeydown)
	document.addEventListener('keydown', globalKeydown)
})

onUnmounted(() => {
	window.removeEventListener('focus', globalKeydown)
	document.removeEventListener('visibilitychange', globalKeydown)
	document.removeEventListener('keydown', globalKeydown)
})
</script>
<template lang="pug">
.container
	.scanner-toolbar(v-if="checkinlist")
		button.btn.btn-primary.btn-scanner.btn-lg(
			type="button",
			:class="{ active: showScanner }",
			@click="toggleScanner"
		)
			span.fa(:class="showScanner ? 'fa-times' : 'fa-qrcode'")
			|  {{ showScanner ? STRINGS['scanner.hide'] : STRINGS['scanner.show'] }}

	h1 {{ props.eventName }}
		small.wwp-badge  {{ STRINGS['wwp.badge'] }}

	Qrscanner(v-if="checkinlist && showScanner", @qr-scanned="handleQRScan")

	CheckinlistSelect(v-if="!checkinlist", @selected="selectList")

	input.form-control.scan-input(
		v-if="checkinlist",
		ref="inputEl",
		v-model="query",
		:placeholder="STRINGS['input.placeholder']",
		@keyup="inputKeyup"
	)

	.panel.panel-primary.check-result(v-if="checkResult !== null && !orderTickets")
		.panel-heading
			a.pull-right(href="#", tabindex="-1", @click.prevent="clear")
				span.fa.fa-close
			h3.panel-title {{ STRINGS['check.headline'] }}
		.panel-body.text-center(v-if="checkLoading")
			span.fa.fa-4x.fa-cog.fa-spin.loading-icon
		.panel-body.text-center(v-else-if="checkError") {{ checkError }}
		.check-result-status(:class="'check-result-' + checkResultColor")
			.check-result-text {{ checkResultText }}
			.check-result-item {{ checkResultItemvar }}
			.check-result-reason(v-if="checkResult.reason_explanation") {{ checkResult.reason_explanation }}
		.attention(v-if="checkResult && checkResult.require_attention")
			span.fa.fa-warning
			| {{ STRINGS['check.attention'] }}
		.panel-body(v-if="checkResult.position")
			.details
				code {{ checkResult.position.order }}-{{ checkResult.position.positionid }}
				h4 {{ checkResult.position.attendee_name }}
				.addons(v-if="checkResultAddons") {{ checkResultAddons }}
				span(v-if="checkResultSubevent") {{ checkResultSubevent }}
					br
				span.secret {{ checkResult.position.secret }}
				span(v-if="checkResult.position.seat")
					br
					| {{ checkResult.position.seat.name }}
				span(v-for="a in checkResult.position.answers")
					span(v-if="a.question.show_during_checkin")
						br
						strong {{ i18nstringLocalize(a.question.question) }}:
						|  {{ formatAnswer(a.answer, a.question) }}
				strong(v-for="t in checkResult.checkin_texts")
					br
					| {{ t }}

	.panel.panel-primary.order-tickets(v-else-if="orderTickets !== null || orderLoading")
		.panel-heading
			a.pull-right(href="#", tabindex="-1", @click.prevent="clear")
				span.fa.fa-close
			h3.panel-title
				| {{ STRINGS['order.headline'] }}
				span(v-if="orderCode")  · {{ orderCode }}
		.panel-body.order-actions(v-if="!orderLoading && orderTickets && orderTickets.length")
			.check-result-flash(v-if="checkResult", :class="'check-result-' + checkResultColor")
				| {{ checkResultText }}
				span(v-if="checkResultItemvar")  — {{ checkResultItemvar }}
			button.btn.btn-success.btn-lg.btn-block(
				v-if="uncheckedOrderTickets.length",
				type="button",
				:disabled="checkAllLoading || checkLoading",
				@click="checkAll"
			)
				span.fa.fa-check-square-o
				|  {{ STRINGS['order.check_all'] }}
				|  ({{ uncheckedOrderTickets.length }})
			p.text-muted.text-center(v-else)
				span.fa.fa-check
				|  {{ STRINGS['order.done'] }}
		.panel-body.text-center(v-if="orderLoading || checkAllLoading")
			span.fa.fa-4x.fa-cog.fa-spin.loading-icon
			p(v-if="checkAllLoading") {{ STRINGS['order.checking_all'] }}
		template(v-else-if="orderTickets")
			.order-ticket-sections(v-if="orderTickets.length")
				OrderTicketGroup(
					v-for="g in groupedOrder.ticketGroups",
					:key="g.key",
					:group="g",
					@selected="(p) => check(p.secret, false, false, false, false)",
					@check-group="checkGroup"
				)
				.order-upselling(v-if="groupedOrder.upsellCategories.length")
					h4.order-upselling-title {{ STRINGS['order.upselling'] }}
					.order-upselling-category(v-for="cat in groupedOrder.upsellCategories", :key="cat.key")
						h5.order-upselling-category-name {{ cat.categoryName }}
						OrderTicketGroup(
							v-for="g in cat.groups",
							:key="g.key",
							:group="g",
							@selected="(p) => check(p.secret, false, false, false, false)",
							@check-group="checkGroup"
						)
			p.list-group-item.text-center(v-if="!orderTickets.length")
				| {{ STRINGS['results.none'] }}

	.panel.panel-primary(v-else-if="lookupLoading || lookupError")
		.panel-heading
			a.pull-right(href="#", tabindex="-1", @click.prevent="clear")
				span.fa.fa-close
			h3.panel-title {{ STRINGS['check.headline'] }}
		.panel-body.text-center(v-if="lookupLoading")
			span.fa.fa-4x.fa-cog.fa-spin.loading-icon
		.check-result-status.check-result-red(v-else)
			.check-result-text {{ lookupError }}

	.modal.modal-unpaid.fade(:class="{ in: showUnpaidModal }", tabindex="-1", role="dialog")
		.modal-dialog(role="document")
			.modal-content(v-if="checkResult && checkResult.position")
				.modal-header
					button.close(type="button", @click="showUnpaidModal = false")
						span.fa.fa-close
					h4.modal-title {{ STRINGS['modal.unpaid.head'] }}
				.modal-body
					p {{ STRINGS['modal.unpaid.text'] }}
				.modal-footer
					button.btn.btn-primary.pull-right(
						type="button",
						@click="check(pendingCheckSecret || checkResult.position.secret, true, false, false, true)"
					) {{ STRINGS['modal.continue'] }}
					button.btn.btn-default(type="button", @click="showUnpaidModal = false")
						| {{ STRINGS['modal.cancel'] }}

	form.modal.modal-questions.fade(
		ref="questionsModalEl",
		:class="{ in: showQuestionsModal }",
		tabindex="-1",
		role="dialog"
	)
		.modal-dialog(role="document")
			.modal-content(v-if="checkResult && checkResult.questions")
				.modal-header
					button.close(type="button", @click="showQuestionsModal = false")
						span.fa.fa-close
					h4.modal-title {{ STRINGS['modal.questions'] }}
				.modal-body
					div(
						v-for="q in checkResult.questions",
						:class="q.type === 'M' ? '' : (q.type === 'B' ? 'checkbox' : 'form-group')"
					)
						label(v-if="q.type !== 'B'", :for="'q_' + q.id")
							| {{ q.question }}
							| {{ q.required ? ' *' : '' }}

						textarea.form-control(
							v-if="q.type === 'T'",
							:id="'q_' + q.id",
							v-model="answers[q.id.toString()]",
							:required="q.required"
						)
						input.form-control(
							v-else-if="q.type === 'N'",
							:id="'q_' + q.id",
							v-model="answers[q.id.toString()]",
							type="number",
							:required="q.required"
						)
						Datefield(
							v-else-if="q.type === 'D'",
							:id="'q_' + q.id",
							v-model="answers[q.id.toString()]",
							:required="q.required"
						)
						Timefield(
							v-else-if="q.type === 'H'",
							:id="'q_' + q.id",
							v-model="answers[q.id.toString()]",
							:required="q.required"
						)
						Datetimefield(
							v-else-if="q.type === 'W'",
							:id="'q_' + q.id",
							v-model="answers[q.id.toString()]",
							:required="q.required"
						)
						select.form-control(
							v-else-if="q.type === 'C'",
							:id="'q_' + q.id",
							v-model="answers[q.id.toString()]",
							:required="q.required"
						)
							option(v-if="!q.required")
							option(v-for="op in q.options", :value="op.id.toString()") {{ op.answer }}
						div(v-else-if="q.type === 'F'")
							em file input not supported
						div(v-else-if="q.type === 'M'")
							.checkbox(v-for="op in q.options")
								label
									input(
										type="checkbox",
										:checked="answers[q.id.toString()] && answers[q.id.toString()].split(',').includes(op.id.toString())",
										@input="answerSetM(q.id.toString(), op.id.toString(), $event.target.checked)"
									)
									|  {{ op.answer }}
						label(v-else-if="q.type === 'B'")
							input(
								type="checkbox",
								:checked="answers[q.id.toString()] === 'true'",
								:required="q.required",
								@input="answers[q.id.toString()] = $event.target.checked.toString()"
							)
							|  {{ q.question }}
							| {{ q.required ? ' *' : '' }}
						select.form-control(
							v-else-if="q.type === 'CC'",
							:id="'q_' + q.id",
							v-model="answers[q.id.toString()]",
							:required="q.required"
						)
							option(v-if="!q.required")
							option(v-for="op in COUNTRIES", :value="op.key") {{ op.value }}
						input.form-control(
							v-else,
							:id="'q_' + q.id",
							v-model="answers[q.id.toString()]",
							:required="q.required"
						)
				.modal-footer
					button.btn.btn-primary.pull-right(
						type="button",
						@click="check(pendingCheckSecret || checkResult.position.secret, true, true, false, false)"
					) {{ STRINGS['modal.continue'] }}
					button.btn.btn-default(type="button", @click="showQuestionsModal = false")
						| {{ STRINGS['modal.cancel'] }}
</template>
