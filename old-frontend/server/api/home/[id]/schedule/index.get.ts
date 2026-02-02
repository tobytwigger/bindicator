export default defineEventHandler(async (event) => {

    const homeId = getRouterParam(event, 'id')

    const schedules = await useDrizzle().select().from(tables.schedules)
        // First, we select all schedules for this home
        .where(eq(tables.schedules.home_id, homeId))
        // Next, we join on all the bins in the chosen schedules.
        .leftJoin(tables.bin_schedules, eq(tables.schedules.id, tables.bin_schedules.schedule_id))
        .leftJoin(tables.bins, eq(tables.bins.id, tables.bin_schedules.bin_id))
        .leftJoin(tables.bin_days, and(
            eq(tables.bins.id, tables.bin_days.bin_id),
            eq(tables.bin_days.schedule_id, tables.schedules.id)
        ))
        .orderBy(tables.bin_days.date)
        .all();

    let formattedSchedules = Object.values(schedules.reduce<Record<number, { schedule: Schedule; bins: Bin[] }>>(
        (acc, row) => {
            const schedule = row.schedules;

            // Set up the schedule entry.
            if (!acc[schedule.id]) {
                acc[schedule.id] = { schedule, bins: {}, next_date: null };
            }

            // Set up the bin entry
            if(!acc[schedule.id].bins[row.bins.id]) {
                acc[schedule.id].bins[row.bins.id] = { bin: row.bins, bin_days: [] };
            }

            if(row.bin_days) {
                let binDay = new Date(Math.ceil(row.bin_days.date));
                // set 'next_date' if binDay is the earliest one after today
                if((acc[schedule.id].next_date === null || binDay < acc[schedule.id].next_date) && binDay > new Date()) {
                    acc[schedule.id].next_date = binDay;
                }

                acc[schedule.id].bins[row.bins.id].bin_days.push({id: row.bin_days.id, date: binDay});
            }

            return acc;
        },
        {},
    ));

    // Convert each formattedSchedules.*.bins to Object.values
    formattedSchedules = formattedSchedules.map(schedule => {
        return {
            ...schedule,
            bins: Object.values(schedule.bins)
        }
    })

    return {
        schedules: formattedSchedules
    }
});
