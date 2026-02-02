export default defineEventHandler(async (event) => {
    const {
        start,
        end,
        repeat_weeks,
        bins
    } = await readBody(event).catch(() => {})

    const homeId = getRouterParam(event, 'id')


    let schedule = await useDrizzle().insert(tables.schedules).values({
        start,
        end,
        repeat_weeks,
        home_id: homeId
    }).returning();

    for (const bin of bins) {
        await useDrizzle().insert(tables.bin_schedules).values({
            bin_id: bin,
            schedule_id: schedule[0].id
        });
    }

    await calculateSchedule(schedule[0])

});
