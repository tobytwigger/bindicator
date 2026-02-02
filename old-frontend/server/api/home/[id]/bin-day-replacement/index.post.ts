import {refreshAllSchedules, replaceWithReplacementDays} from "~/server/utils/scheduleCalculator";

export default defineEventHandler(async (event) => {
    const body = await readBody(event).catch(() => {})
    const homeId = getRouterParam(event, 'id')

    await useDrizzle().insert(tables.bin_day_replacements).values({
        replace: body.replace,
        with: body.with,
        home_id: homeId
    });

    await refreshAllSchedules(homeId)
});
