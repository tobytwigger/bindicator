export default defineEventHandler(async (event) => {
    const id = getRouterParam(event, 'id')
    const scheduleId = getRouterParam(event, 'schedule_id')

    let schedule = await useDrizzle().select().from(tables.schedules).where(eq(tables.schedules.id, scheduleId)).get();

    if(!schedule) {
        throw new NotFoundError(`Schedule with id ${scheduleId} not found`);
    }

    await calculateSchedule(schedule)
});