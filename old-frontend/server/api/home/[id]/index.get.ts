import {eq} from 'drizzle-orm';

export default defineEventHandler(async (event) => {
    const id = getRouterParam(event, 'id')
    let home = await useDrizzle().select().from(tables.homes).where(eq(tables.homes.id, id)).get();



    return {
        home: await useDrizzle().select().from(tables.homes).where(eq(tables.homes.id, id)).get(),
        has_schedule: (await useDrizzle().select().from(tables.schedules).where(eq(tables.schedules.home_id, id))).length > 0,
        has_bins: (await useDrizzle().select().from(tables.bins).where(eq(tables.bins.home_id, id))).length > 0
    };
});