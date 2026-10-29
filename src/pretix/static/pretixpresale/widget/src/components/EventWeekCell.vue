<script setup lang="ts">
import { computed, inject } from 'vue'
import type { DayEntry } from '~/types'
import { StoreKey } from '~/sharedStore'
import EventCalendarEvent from './EventCalendarEvent.vue'

const props = defineProps<{
	day: DayEntry | null
	mobile: boolean // TODO inject?
}>()

const store = inject(StoreKey)!

const id = computed(() => props.day ? `${store.htmlId}-${props.day.date}` : '')

const dayhead = computed(() => {
	if (!props.day) return ''
	return props.day.day_formatted
})

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

const classObject = computed(() => {
	const o: Record<string, boolean> = {}
	if (props.day && props.day.events.length > 0 && dayAvailability.value) {
		o['pretix-widget-has-events'] = true
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

function selectDay () {
	if (!props.day || !props.day.events.length || !props.mobile || !dayOpenable.value) return

	// Display-only events are not navigable to the shop; show the list detail view instead
	// (same as multi-event days) so a single subevent day remains viewable.
	const ev = props.day.events[0]
	if (props.day.events.length === 1 && ev.clickable !== false) {
		// TODO store mutation bad
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
</script>
<template lang="pug">
div(:class="classObject", @click.prevent.stop="selectDay")
	.pretix-widget-event-calendar-day(v-if="day", :id="id") {{ dayhead }}
	.pretix-widget-event-calendar-events(v-if="day")
		EventCalendarEvent(
			v-for="e in day.events",
			:key="e.event_url",
			:event="e",
			:describedby="id"
		)
</template>
<style lang="sass">
</style>
