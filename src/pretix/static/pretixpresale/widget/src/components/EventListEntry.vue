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
	.pretix-widget-event-list-entry-crowd {{ event.crowd ? `Verwachte drukte: ${event.crowd}` : '' }}
	.pretix-widget-event-list-entry-date {{ event.date_range }}
	//- hidden by css for now, but used by a few people
	.pretix-widget-event-list-entry-location {{ location }}
	.pretix-widget-event-list-entry-availability
		span {{ event.availability.text }}
</template>
<style lang="sass">
.pretix-widget-event-list-entry
	display: flex
	flex-direction: row
	flex-wrap: wrap
	align-items: center
	padding: 6px 0
	gap: 0

	.pretix-widget-event-list-entry-name
		width: 55%
		padding: 4px 8px 4px 5px
		box-sizing: border-box
		font-weight: 600

	.pretix-widget-event-list-entry-crowd
		width: 45%
		padding: 4px 5px
		box-sizing: border-box
		text-align: right
		font-size: 90%
		opacity: 0.85
		min-height: 1.2em

	.pretix-widget-event-list-entry-date
		width: 55%
		padding: 2px 8px 4px 5px
		box-sizing: border-box
		color: #666
		font-size: 90%

	.pretix-widget-event-list-entry-availability
		width: 45%
		padding: 2px 5px 4px
		box-sizing: border-box
		text-align: right
		margin-left: 0

@media (max-width: 480px)
	.pretix-widget-event-list-entry
		.pretix-widget-event-list-entry-name,
		.pretix-widget-event-list-entry-date
			width: 100%
			padding-right: 5px

		.pretix-widget-event-list-entry-crowd,
		.pretix-widget-event-list-entry-availability
			width: 100%
			text-align: left
			padding-left: 5px
</style>
