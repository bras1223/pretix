<script setup lang="ts">
import { computed, inject, ref } from 'vue'
import { StoreKey } from '~/sharedStore'
import { STRINGS } from '~/i18n'

const store = inject(StoreKey)!

const voucherinput = ref<HTMLInputElement>()
const localVoucher = ref('')

const idVoucherInput = computed(() => `${store.htmlId}-voucher-input`)
const ariaLabelledby = computed(() => `${store.htmlId}-voucher-headline`)

const hiddenParams = computed(() => {
	const params = new URL(store.getVoucherFormTarget()).searchParams
	params.delete('iframe')
	params.delete('take_cart_id')
	return [...params.entries()]
})

function handleRedeem (event: Event) {
	store.redeem(localVoucher.value, event)
}

defineExpose({
	focus: () => voucherinput.value?.focus(),
})
</script>
<template lang="pug">
form(
	method="get",
	:action="store.getVoucherFormTarget()",
	target="_blank"
)
	.pretix-widget-voucher
		h3.pretix-widget-voucher-headline(:id="ariaLabelledby") {{ STRINGS.redeem_voucher }}
		.pretix-widget-voucher-text(
			v-if="store.voucherExplanationText",
			v-html="store.voucherExplanationText"
		)
		.pretix-widget-voucher-input-wrap
			input.pretix-widget-voucher-input(
				:id="idVoucherInput",
				ref="voucherinput",
				v-model="localVoucher",
				type="text",
				name="voucher",
				:placeholder="STRINGS.voucher_code",
				:aria-labelledby="ariaLabelledby"
			)
		input(
			v-for="p in hiddenParams",
			:key="p[0]",
			type="hidden",
			:name="p[0]",
			:value="p[1]"
		)
		.pretix-widget-voucher-button-wrap
			button(@click="handleRedeem") {{ STRINGS.redeem }}
		.pretix-widget-clear
</template>
<style lang="sass">
</style>
