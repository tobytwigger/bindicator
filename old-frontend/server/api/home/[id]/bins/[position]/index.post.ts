export default defineEventHandler(async (event) => {
    const {
        humanName,
        option,
    } = await readBody(event).catch(() => {})

    const homeId = getRouterParam(event, 'id')
    const position = getRouterParam(event, 'position')

    const bin = await useDrizzle().select().from(tables.bins)
        .where(and(
            eq(tables.bins.home_id, homeId),
            eq(tables.bins.position, position)
        ))
        .get();

    if(bin) {
        await useDrizzle().update(tables.bins).set({
            name: humanName,
            council_name: option,
        }).where(eq(tables.bins.id, bin.id));
    } else {
        await useDrizzle().insert(tables.bins).values({
            name: humanName,
            council_name: option,
            position: position,
            home_id: homeId
        });
    }


})
