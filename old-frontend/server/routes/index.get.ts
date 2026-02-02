import {useDrizzle} from "~/server/utils/drizzle";

export default defineEventHandler(async (event) => {
    // return sendRedirect(event, "https://example.com");
    let redirectTo = '/home'
    if(event.path === '/') {
        const homes = await useDrizzle().select().from(tables.homes);
        if(homes.length > 0) {
            let activeHomes = homes.filter(h => h.active)
            if(activeHomes.length > 0) {
                redirectTo = '/home/' + activeHomes[0].id
            }
        } else {
            redirectTo = '/home/create';
        }
    }
    console.log(redirectTo)
    return sendRedirect(event, redirectTo)

})