export default defineEventHandler(async (event) => {

    const homeId = getRouterParam(event, 'id')

    const binDayReplacements = await useDrizzle().select().from(tables.bin_day_replacements)
        .where(eq(tables.bin_day_replacements.home_id, homeId));

    return {
        bin_day_replacements: binDayReplacements
    }
});
