import {eq} from 'drizzle-orm';

export default defineEventHandler(async (event) => {
    const homeId = getRouterParam(event, 'id')
    const position = getRouterParam(event, 'position')

    await useDrizzle().delete(tables.bins).where(and(
        eq(tables.bins.home_id, homeId), eq(tables.bins.position, position)
    ))
});