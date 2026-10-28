import type { ItemCategory, Position } from './api'
import { STRINGS, i18nstringLocalize } from './i18n'

export interface TicketLine {
	position: Position
	addons: Position[]
}

export interface TicketGroup {
	key: string
	itemName: string
	variationName: string
	count: number
	lines: TicketLine[]
	unchecked: Position[]
}

export interface UpsellCategoryGroup {
	key: string
	categoryName: string
	groups: TicketGroup[]
}

function categoryMap (categories: ItemCategory[]): Map<number, ItemCategory> {
	return new Map(categories.map(c => [c.id, c]))
}

export function isUpsellingPosition (position: Position, categories: ItemCategory[]): boolean {
	if (position.addon_to) return false
	const catId = position.item.category
	if (catId == null) {
		// No category: treat non-admission top-level products as upselling extras
		return position.item.admission === false
	}
	const cat = categoryMap(categories).get(catId)
	if (!cat) return position.item.admission === false
	if (cat.is_addon) return false
	if (cat.cross_selling_mode === 'only' || cat.cross_selling_mode === 'both') return true
	return false
}

function itemKey (position: Position): string {
	const itemId = position.item.id ?? i18nstringLocalize(position.item.name)
	const varId = position.variation?.id ?? position.variation?.value ?? ''
	return `${itemId}::${varId}`
}

function itemName (position: Position): string {
	return position.item.internal_name || i18nstringLocalize(position.item.name)
}

function variationName (position: Position): string {
	return position.variation ? i18nstringLocalize(position.variation.value) : ''
}

function buildGroups (positions: Position[]): TicketGroup[] {
	const byKey = new Map<string, TicketGroup>()
	for (const position of positions) {
		const key = itemKey(position)
		let group = byKey.get(key)
		if (!group) {
			group = {
				key,
				itemName: itemName(position),
				variationName: variationName(position),
				count: 0,
				lines: [],
				unchecked: [],
			}
			byKey.set(key, group)
		}
		group.count++
		group.lines.push({ position, addons: [] })
		if (!position.checkins?.length) {
			group.unchecked.push(position)
		}
	}
	return [...byKey.values()]
}

function attachAddons (groups: TicketGroup[], addons: Position[]): void {
	const lineByParentId = new Map<number, TicketLine>()
	for (const group of groups) {
		for (const line of group.lines) {
			lineByParentId.set(line.position.id, line)
		}
	}
	for (const addon of addons) {
		const parent = addon.addon_to != null ? lineByParentId.get(addon.addon_to) : undefined
		if (parent) {
			parent.addons.push(addon)
		}
	}
}

export function groupOrderTickets (
	positions: Position[],
	categories: ItemCategory[]
): { ticketGroups: TicketGroup[], upsellCategories: UpsellCategoryGroup[] } {
	const addons = positions.filter(p => p.addon_to != null)
	const topLevel = positions.filter(p => p.addon_to == null)
	const upsell = topLevel.filter(p => isUpsellingPosition(p, categories))
	const tickets = topLevel.filter(p => !isUpsellingPosition(p, categories))

	const ticketGroups = buildGroups(tickets)
	attachAddons(ticketGroups, addons)

	const cats = categoryMap(categories)
	const byCategory = new Map<string, { categoryName: string, positions: Position[] }>()
	for (const position of upsell) {
		const catId = position.item.category
		const cat = catId != null ? cats.get(catId) : undefined
		const key = cat ? String(cat.id) : 'other'
		const categoryName = cat
			? (cat.internal_name || i18nstringLocalize(cat.name))
			: STRINGS['order.extras']
		let bucket = byCategory.get(key)
		if (!bucket) {
			bucket = { categoryName, positions: [] }
			byCategory.set(key, bucket)
		}
		bucket.positions.push(position)
	}

	const upsellCategories: UpsellCategoryGroup[] = []
	for (const [key, bucket] of byCategory) {
		const groups = buildGroups(bucket.positions)
		attachAddons(groups, addons)
		upsellCategories.push({
			key,
			categoryName: bucket.categoryName,
			groups,
		})
	}

	return { ticketGroups, upsellCategories }
}
