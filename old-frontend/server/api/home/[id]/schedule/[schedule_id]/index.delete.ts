import {eq} from 'drizzle-orm';

export default defineEventHandler(async (event) => {
    const id = getRouterParam(event, 'id')
    const scheduleId = getRouterParam(event, 'schedule_id')

    await useDrizzle().delete(tables.bin_days)
        .where(eq(tables.bin_days.schedule_id, scheduleId))

    await useDrizzle().delete(tables.bin_schedules)
        .where(eq(tables.bin_schedules.schedule_id, scheduleId))

    await useDrizzle().delete(tables.schedules)
        .where(eq(tables.schedules.id, scheduleId))
});