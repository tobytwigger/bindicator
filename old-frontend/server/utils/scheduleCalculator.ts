import { gt, gte, lte } from "drizzle-orm";

export async function refreshAllSchedules(homeId: number) {
    let schedules = await useDrizzle().select().from(tables.schedules);

    for (const schedule of schedules) {
        await calculateSchedule(schedule);
    }

}

export async function calculateSchedule(schedule: Schedule) {
    let binReplacements = await getDatesToReplace(schedule.home_id);
    console.log(binReplacements);
    // Calculate the schedule for the next 6 months.

    // First, we clear all current schedule entries for this schedule.
    await useDrizzle().delete(tables.bin_days)
        .where(eq(tables.bin_days.schedule_id, schedule.id))

    const start = new Date(schedule.start)

    const dates: Date[] = [new Date(schedule.start)]
    // We will calculate the schedule for the next 6 months.

    // We finish the schedule either when it ends, or in 6 months time.
    const finish = schedule.end ? new Date(schedule.end) : new Date(start.getTime() + 6 * 30 * 24 * 60 * 60 * 1000)

    const currentDate = start

    while (currentDate < finish) {
        // We calculate the next date.
        currentDate.setDate(currentDate.getDate() + 7 * schedule.repeat_weeks)
        dates.push(new Date(currentDate))
    }

    const bins = await useDrizzle().select().from(tables.bin_schedules)
        .where(eq(tables.bin_schedules.schedule_id, schedule.id))
        .all()

    // For each date, we save the bin days
    for (const date of dates) {
        for (const bin of bins) {
            await useDrizzle().insert(tables.bin_days).values({
                bin_id: bin.bin_id,
                schedule_id: schedule.id,
                home_id: schedule.home_id,
                date
            })
        }
    }

    await replaceWithReplacementDays(schedule.home_id);

}

export async function getDatesToReplace(homeId: number) {
    // Get all bin_day_replacements where the replace date is in the future.
    let binDayReplacements = await useDrizzle().select().from(tables.bin_day_replacements)
        .where(and(
            eq(tables.bin_day_replacements.home_id, homeId),
            or(
                gt(tables.bin_day_replacements.replace, new Date()),
                gt(tables.bin_day_replacements.with, new Date())
            )
        ))
        .all()

    // Return with the replacement date as the key and the with date as the value.
    let replacements = {}

    for(const replacement of binDayReplacements) {
        replacements[replacement.replace] = replacement.with
    }

    return replacements;


}

export async function replaceWithReplacementDays(homeId: number) {
    // Iterate through all bin_day_replacements where either with or replace is in the future.
    console.log('redoing the replacement day schedule')

    let binDayReplacements = await useDrizzle().select().from(tables.bin_day_replacements)
        .where(and(
            eq(tables.bin_day_replacements.home_id, homeId),
            or(
                gt(tables.bin_day_replacements.replace, new Date()),
                gt(tables.bin_day_replacements.with, new Date())
            )
        ))
        .all()

    for(const replacement of binDayReplacements) {
        if(replacement.replace && replacement.with) {
            let startOfReplaceDay = (new Date(replacement.replace))
                .setHours(0, 0, 0, 0)
            let endOfReplaceDay = (new Date(replacement.replace))
                .setHours(23, 59, 59, 999)
            let startOfWithDay = (new Date(replacement.with))
                .setHours(0, 0, 0, 0)
            let endOfWithDay = (new Date(replacement.with))
                .setHours(23, 59, 59, 999)

console.log('-----------------------------------------------------------------------------------------------------------------------')
            // Find all bin_days that match the replacement date.
            let binDays = await useDrizzle().select().from(tables.bin_days)
                .where(and(
                    eq(tables.bin_days.home_id, homeId),
                    or(
                        and(
                            gte(tables.bin_days.date, startOfReplaceDay),
                            lte(tables.bin_days.date, endOfReplaceDay)
                        ),
                        and(
                            gte(tables.bin_days.date, startOfWithDay),
                            lte(tables.bin_days.date, endOfWithDay)
                        )
                    )
                ))
                .all()
            console.log('-----------------------------------------------------------------------------------------------------------------------')

            // TODO Log this SQL, work out why it's not selecting the right bin days.
            // TODO CHeck the schedule updates properly
            console.log(binDays);
            // For each bin_day, update the date to the replacement date.
            for(const binDay of binDays) {
                await useDrizzle().update(tables.bin_days)
                    .set({date: new Date(replacement.with).getTime()})
                    .where(eq(tables.bin_days.id, binDay.id))
            }
        }
    }

    // console.log(homeId);
}