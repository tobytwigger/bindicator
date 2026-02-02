import {eq, ne} from 'drizzle-orm';

export default defineEventHandler(async (event) => {
    const id = getRouterParam(event, 'id')

    await useDrizzle().update(tables.homes).set({active: true}).where(eq(tables.homes.id, id));
    await useDrizzle().update(tables.homes).set({active: false}).where(ne(tables.homes.id, id));
});