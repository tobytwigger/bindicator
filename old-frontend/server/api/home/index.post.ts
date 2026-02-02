import {eq} from "drizzle-orm";

export default defineEventHandler(async (event) => {
    const {
        name,
        council,
        councilData,
        timeout,
        putOutDayBefore
    } = await readBody(event).catch(() => {})

    let alreadyAnActiveHome = await useDrizzle().select().from(tables.homes).where(eq(tables.homes.active, true)).get()

    const home = await useDrizzle().insert(tables.homes).values({
        name,
        council,
        council_data: councilData,
        active: !alreadyAnActiveHome?.id,
        timeout,
        put_out_day_before: putOutDayBefore
    }).returning().get()

    return home;
})
