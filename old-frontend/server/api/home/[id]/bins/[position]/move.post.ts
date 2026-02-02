import {eq} from 'drizzle-orm';

export default defineEventHandler(async (event) => {
    const homeId = getRouterParam(event, 'id')
    const position = getRouterParam(event, 'position')
    const {direction} = await readBody(event).catch(() => {
    })

    if (homeId === undefined || position === undefined || direction === undefined) {
        throw new Error('Missing required')
    }

    if (direction === 'forwards') {
        swap(homeId, parseInt(position), parseInt(position) + 1)
    } else if (direction === 'backwards') {
        swap(homeId, parseInt(position), parseInt(position) - 1)
    }
});

async function swap(homeId: string, fromPosition: number, toPosition: number) {
    const fromBin = await useDrizzle().select().from(tables.bins).where(and(
        eq(tables.bins.home_id, homeId), eq(tables.bins.position, fromPosition)
    )).get()

    const toBin = await useDrizzle().select().from(tables.bins).where(and(
        eq(tables.bins.home_id, homeId), eq(tables.bins.position, toPosition)
    )).get()

    if (fromBin === undefined) {
        throw new Error('Invalid swap')
    }

    await useDrizzle().update(tables.bins).set({
        position: 99999999
    }).where(eq(tables.bins.id, fromBin.id)).execute()

    if (toBin !== undefined) {
        await useDrizzle().update(tables.bins).set({
            position: fromPosition
        }).where(eq(tables.bins.id, toBin.id)).execute()
    }

    await useDrizzle().update(tables.bins).set({
        position: toPosition
    }).where(eq(tables.bins.id, fromBin.id)).execute()
}