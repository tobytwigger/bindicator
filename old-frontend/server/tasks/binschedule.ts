export default defineTask({
    meta: {
        name: "binschedule",
        description: "Update the schedule for all bins",
    },
    async run({ payload, context }) {
        console.log("Running bin schedule task...");

        let schedules = await useDrizzle().select().from(tables.schedules);

        for (const schedule of schedules) {
            await calculateSchedule(schedule);
        }

        return { result: "Success" };
    },
});