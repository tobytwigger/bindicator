import {eq} from 'drizzle-orm';

export default defineEventHandler(async (event) => {
    const id = getRouterParam(event, 'id')

    return {bins: await useDrizzle().select().from(tables.bins).where(eq(tables.bins.home_id, id))};
});