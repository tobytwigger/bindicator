import {eq} from 'drizzle-orm';
import {testHome} from "~/server/utils/python";

export default defineEventHandler(async (event) => {
    const id = getRouterParam(event, 'id')

    if(!id) {
        throw new Error('id is required');
    }

    const data = await testHome(id);

    return data;
});