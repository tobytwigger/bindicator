import {eq} from 'drizzle-orm';
import {refreshAllSchedules, replaceWithReplacementDays} from "~/server/utils/scheduleCalculator";

export default defineEventHandler(async (event) => {
    const homeId = getRouterParam(event, 'id')
    const binDayReplacementId = getRouterParam(event, 'bin_day_replacement_id')

    await useDrizzle().delete(tables.bin_day_replacements)
        .where(eq(tables.bin_day_replacements.id, binDayReplacementId))

    await refreshAllSchedules(homeId)

});