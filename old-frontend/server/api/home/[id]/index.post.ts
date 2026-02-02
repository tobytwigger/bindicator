import {eq} from "drizzle-orm";

export default defineEventHandler(async (event) => {
    const body = await readBody(event).catch(() => {})

    const id = getRouterParam(event, 'id')
    let home = await useDrizzle().select().from(tables.homes).where(eq(tables.homes.id, id)).get();

    if(home) {
        home = await useDrizzle().update(tables.homes).set({
            name: body.name,
            council: body.council,
            council_data: body.councilData,
            timeout: body.timeout,
            put_out_day_before: body.putOutDayBefore
        }).where(eq(tables.homes.id, id)).returning().get()
    } else {

        const home = await useDrizzle().insert(tables.homes).values({
            name: body.name,
            council: body.council,
            council_data: body.councilData,
            active: !alreadyAnActiveHome?.id,
            timeout: body.timeout,
            put_out_day_before: body.putOutDayBefore
        }).returning().get()
    }

    return home;
})
