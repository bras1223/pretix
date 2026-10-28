<script setup lang="ts">
import { computed, inject } from 'vue'
import type { EventEntry } from '~/types'
import { StoreKey } from '~/sharedStore'

const props = defineProps<{
	event: EventEntry
}>()

const store = inject(StoreKey)!

const isClickable = computed(() => props.event.clickable !== false)

const classObject = computed(() => {
	const o: Record<string, boolean> = {
		'pretix-widget-event-list-entry': true,
		'pretix-widget-event-not-clickable': !isClickable.value,
	}
	o[`pretix-widget-event-availability-${props.event.availability.color}`] = true
	if (props.event.availability.reason) {
		o[`pretix-widget-event-availability-${props.event.availability.reason}`] = true
	}
	return o
})

const location = computed(() => props.event.location.replace(/\s*\n\s*/g, ', '))

function select () {
	if (!isClickable.value) return
	store.parentStack.push(store.targetUrl)
	store.targetUrl = props.event.event_url
	store.error = null
	store.subevent = props.event.subevent ?? null
	store.loading++
	store.reload()
}
</script>
<template lang="pug">
component(
	:is="isClickable ? 'a' : 'span'",
	:href="isClickable ? '#' : undefined",
	:class="classObject",
	:aria-disabled="!isClickable ? 'true' : undefined",
	@click.prevent.stop="select"
)
	.pretix-widget-event-list-entry-name {{ event.name }}
	.pretix-widget-event-list-entry-date {{ event.date_range }}
	//- hidden by css for now, but used by a few people
	.pretix-widget-event-list-entry-location {{ location }}
	.pretix-widget-event-list-entry-availability
		span {{ event.availability.text }}
</template>
<style lang="sass">
</style>
