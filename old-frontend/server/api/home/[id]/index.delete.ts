import {eq} from 'drizzle-orm';

export default defineEventHandler(async (event) => {
    const id = getRouterParam(event, 'id')

    await useDrizzle().delete(tables.bins).where(eq(tables.bins.home_id, id))

    await useDrizzle().delete(tables.homes).where(eq(tables.homes.id, id))
});