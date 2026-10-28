<script setup lang="ts">
import { computed } from 'vue'
import type { Position } from '../api'
import type { TicketGroup } from '../orderGroups'
import { STRINGS, i18nstringLocalize } from '../i18n'

const props = defineProps<{
	group: TicketGroup
}>()

const emit = defineEmits<{
	selected: [position: Position]
	checkGroup: [positions: Position[]]
}>()

const title = computed(() => {
	if (props.group.variationName) {
		return `${props.group.itemName} – ${props.group.variationName}`
	}
	return props.group.itemName
})

const allRedeemed = computed(() => props.group.unchecked.length === 0)

/** Bundle identical add-ons across tickets in this group */
const bundledAddons = computed(() => {
	const map = new Map<string, {
		key: string
		label: string
		count: number
		unchecked: Position[]
		allRedeemed: boolean
	}>()

	for (const line of props.group.lines) {
		for (const addon of line.addons) {
			const itemId = addon.item.id ?? i18nstringLocalize(addon.item.name)
			const varId = addon.variation?.id ?? (addon.variation ? i18nstringLocalize(addon.variation.value) : '')
			const key = `${itemId}::${varId}`
			const name = addon.item.internal_name || i18nstringLocalize(addon.item.name)
			const label = addon.variation
				? `${name} – ${i18nstringLocalize(addon.variation.value)}`
				: name
			let entry = map.get(key)
			if (!entry) {
				entry = { key, label, count: 0, unchecked: [], allRedeemed: true }
				map.set(key, entry)
			}
			entry.count++
			if (addon.checkins?.length) {
				// keep allRedeemed true only if every one is redeemed
			} else {
				entry.allRedeemed = false
				entry.unchecked.push(addon)
			}
		}
	}
	return [...map.values()]
})

function activateGroup () {
	if (props.group.unchecked.length) {
		emit('checkGroup', props.group.unchecked)
	} else if (props.group.lines[0]) {
		emit('selected', props.group.lines[0].position)
	}
}

function activateAddon (unchecked: Position[], sample?: Position) {
	if (unchecked.length) {
		emit('checkGroup', unchecked)
	} else if (sample) {
		emit('selected', sample)
	}
}

function addonSample (key: string): Position | undefined {
	for (const line of props.group.lines) {
		for (const addon of line.addons) {
			const itemId = addon.item.id ?? i18nstringLocalize(addon.item.name)
			const varId = addon.variation?.id ?? (addon.variation ? i18nstringLocalize(addon.variation.value) : '')
			if (`${itemId}::${varId}` === key) return addon
		}
	}
	return undefined
}
</script>
<template lang="pug">
.order-ticket-group(:class="{ 'is-redeemed': allRedeemed }")
	a.order-ticket-group-main(href="#", @click.prevent="activateGroup")
		.order-ticket-group-title
			span.order-ticket-group-qty {{ group.count }}x
			|  {{ title }}
		.order-ticket-group-meta
			.status(:class="allRedeemed ? 'status-redeemed' : 'status-p'")
				| {{ allRedeemed ? STRINGS['status.redeemed'] : STRINGS['status.p'] }}
	.order-ticket-addons(v-if="bundledAddons.length")
		.order-ticket-addons-label {{ STRINGS['order.addons'] }}
		a.order-ticket-addon(
			v-for="addon in bundledAddons",
			:key="addon.key",
			href="#",
			:class="{ redeemed: addon.allRedeemed }",
			@click.prevent="activateAddon(addon.unchecked, addonSample(addon.key))"
		)
			span.addon-name
				span.addon-qty {{ addon.count }}x
				|  {{ addon.label }}
			span.status(:class="addon.allRedeemed ? 'status-redeemed' : 'status-p'")
				| {{ addon.allRedeemed ? STRINGS['status.redeemed'] : STRINGS['status.p'] }}
</template>
