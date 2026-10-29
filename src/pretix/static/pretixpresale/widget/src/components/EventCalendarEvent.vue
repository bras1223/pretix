<script setup lang="ts">
import { computed, inject } from 'vue'
import type { EventEntry } from '~/types'
import { StoreKey } from '~/sharedStore'

const props = defineProps<{
	event: EventEntry
	describedby?: string
}>()

const store = inject(StoreKey)!

const isClickable = computed(() => props.event.clickable !== false)

const classObject = computed(() => {
	const o: Record<string, boolean> = {
		'pretix-widget-event-calendar-event': true,
	}
	o[`pretix-widget-event-availability-${props.event.availability.color}`] = true
	if (props.event.availability.reason) {
		o[`pretix-widget-event-availability-${props.event.availability.reason}`] = true
	}
	return o
})

function select () {
	if (!isClickable.value) {
		// Display-only: show list detail instead of opening the shop
		store.events = [props.event]
		store.view = 'events'
		return
	}
	store.parentStack.push(store.targetUrl)
	store.targetUrl = props.event.event_url
	store.error = null
	store.subevent = props.event.subevent ?? null
	store.loading++
	store.reload()
}
</script>
<template lang="pug">
a(
	href="#",
	:class="classObject",
	:aria-describedby="describedby",
	@click.prevent.stop="select"
)
	.pretix-widget-event-calendar-event-row
		strong.pretix-widget-event-calendar-event-name {{ event.name }}
		.pretix-widget-event-calendar-event-availability(v-if="!event.continued && event.availability.text") {{ event.availability.text }}
	.pretix-widget-event-calendar-event-meta(v-if="!event.continued && (event.time || event.crowd)")
		.pretix-widget-event-calendar-event-date(v-if="event.time") {{ event.time }}
		.pretix-widget-event-calendar-event-crowd(v-if="event.crowd") {{ event.crowd }}
</template>
<style lang="sass">
.pretix-widget-event-calendar-event-row
	display: flex
	align-items: baseline
	justify-content: space-between
	gap: 8px

.pretix-widget-event-calendar-event-name
	flex: 1 1 auto
	min-width: 0

.pretix-widget-event-calendar-event-availability
	flex: 0 0 auto
	font-size: 75%
	font-weight: bold
	white-space: nowrap

.pretix-widget-event-calendar-event-meta
	display: flex
	justify-content: space-between
	gap: 8px
	margin-top: 2px
	font-size: 85%
	opacity: 0.9

.pretix-widget-event-calendar-event-crowd
	margin-left: auto
	text-align: right
</style>
