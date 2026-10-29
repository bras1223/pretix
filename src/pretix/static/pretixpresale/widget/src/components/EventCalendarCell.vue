<script setup lang="ts">
import { computed, inject, ref, onMounted, watch } from 'vue'
import type { DayEntry } from '~/types'
import { StoreKey } from '~/sharedStore'
import EventCalendarEvent from './EventCalendarEvent.vue'

const props = defineProps<{
	day: DayEntry | null
	mobile: boolean
}>()

const store = inject(StoreKey)!
const cellEl = ref<HTMLTableCellElement>()

const daynum = computed(() => {
	if (!props.day) return ''
	return props.day.date.substr(8)
})

const dateStr = computed(() => props.day ? new Date(props.day.date).toLocaleDateString() : '')

const dayAvailability = computed(() => {
	if (!props.day || !props.day.events.length) return null
	let best: 'red' | 'orange' | 'green' = 'red'
	let allLow = true
	for (const ev of props.day.events) {
		if (ev.availability.color === 'green') {
			best = 'green'
			if (ev.availability.reason !== 'low') {
				allLow = false
			}
		} else if (ev.availability.color === 'orange' && best !== 'green') {
			best = 'orange'
		}
	}
	return { best, allLow }
})

const dayOpenable = computed(() => !!dayAvailability.value && dayAvailability.value.best !== 'red')

const role = computed(() => !props.day || !props.day.events.length || !props.mobile || !dayOpenable.value ? 'cell' : 'button')

const tabindex = computed(() => role.value === 'button' ? '0' : '-1')

const classObject = computed(() => {
	const o: Record<string, boolean> = {}
	if (props.day && props.day.events.length > 0 && dayAvailability.value) {
		o['pretix-widget-has-events'] = true // TODO static
		o[`pretix-widget-day-availability-${dayAvailability.value.best}`] = true
		if (dayAvailability.value.best === 'green' && dayAvailability.value.allLow) {
			o['pretix-widget-day-availability-low'] = true
		}
		if (!dayOpenable.value) {
			o['pretix-widget-day-not-openable'] = true
		}
	}
	return o
})

function selectDay (e: Event) {
	if (!props.day || !props.day.events.length || !props.mobile || !dayOpenable.value) return
	e.preventDefault()
	e.stopPropagation()

	// TODO decopypasta
	// Display-only events are not navigable to the shop; show the list detail view instead
	// (same as multi-event days) so a single subevent day remains viewable.
	const ev = props.day.events[0]
	if (props.day.events.length === 1 && ev.clickable !== false) {
		store.parentStack.push(store.targetUrl)
		store.targetUrl = ev.event_url
		store.error = null
		store.subevent = ev.subevent ?? null
		store.loading++
		store.reload()
	} else {
		store.events = props.day.events
		store.view = 'events'
	}
}

function onKeyDown (e: KeyboardEvent) {
	const keyDown = e.key ?? e.keyCode
	if (keyDown === 'Enter' || keyDown === 13 || ['Spacebar', ' '].includes(keyDown as string) || keyDown === 32) {
		// (prevent default so the page doesn't scroll when pressing space)
		e.preventDefault()
		selectDay(e)
	}
}

function attachListeners () {
	if (role.value === 'button' && cellEl.value) {
		cellEl.value.addEventListener('click', selectDay)
		cellEl.value.addEventListener('keydown', onKeyDown)
	}
}

function detachListeners () {
	if (cellEl.value) {
		cellEl.value.removeEventListener('click', selectDay)
		cellEl.value.removeEventListener('keydown', onKeyDown)
	}
}

onMounted(() => {
	attachListeners()
})

// TODO why different from old version?
watch(role, (newValue, oldValue) => {
	if (newValue === 'button' && oldValue !== 'button') {
		attachListeners()
	} else if (newValue !== 'button' && oldValue === 'button') {
		detachListeners()
	}
})
</script>
<template lang="pug">
td(
	ref="cellEl",
	:class="classObject",
	:role="role",
	:tabindex="tabindex",
	:aria-label="dateStr"
)
	.pretix-widget-event-calendar-day(v-if="day", :aria-label="dateStr") {{ daynum }}
	.pretix-widget-event-calendar-events(v-if="day")
		EventCalendarEvent(v-for="e in day.events", :key="e.event_url+'-'+(e.subevent||'')", :event="e")
</template>
<style lang="sass">
</style>
