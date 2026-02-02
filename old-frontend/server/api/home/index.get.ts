export default defineEventHandler(async (event) => {
    let homes = await useDrizzle().select().from(tables.homes);
    return {homes: homes};
})
