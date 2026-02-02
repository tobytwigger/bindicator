import {eq} from 'drizzle-orm';
import {getBinOptions} from "~/server/utils/python";

export default defineEventHandler(async (event) => {
    const id = getRouterParam(event, 'id')

    if(!id) {
        throw new Error('id is required');
    }

    let options = await getBinOptions(id);

    return {
        options: options.options
    }
});