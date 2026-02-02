<script setup lang="ts">

import {ScheduleXCalendar} from '@schedule-x/vue'
import {
    createCalendar,
    createViewMonthGrid,
    createViewMonthAgenda,
} from '@schedule-x/calendar'
import '@schedule-x/theme-default/dist/index.css'
import {format} from "date-fns";

const colorMode = useColorMode()

watch(() => colorMode.value, () => {
    createCalendarFromSchedule();
})

const props = defineProps<{
    schedules: {
        schedule: Schedule,
        bins: {
            bin: Bin,
            bin_days: {
                id: number,
                date: string,
            }[]
        }[]
    }[]
}>();

const jsonOfSchedules = computed(() => {
    return JSON.stringify(props.schedules)
});

watch(() => jsonOfSchedules.value, () => {
    createCalendarFromSchedule();
})

let calendarApp = null;

const shouldShowCalendar = ref<boolean>(false);

watch(() => props.schedules, () => {
    createCalendarFromSchedule();
})

const createCalendarFromSchedule = () => {
    shouldShowCalendar.value = false

    nextTick(() => {
// Each bin should be a different calendar
        const calendars = [];

        console.log(colorMode.value === 'dark')

        // Iterate through props.schedules
        for (let schedule of props.schedules) {
            for (let bin of schedule.bins) {
                if (!calendars[bin.bin.name]) {
                    calendars[bin.bin.name] = {
                        colorName: bin.bin.name,
                        lightColors: {
                            main: '#f9d71c',
                            container: '#fff5aa',
                            onContainer: '#594800',
                        },
                        darkColors: {
                            main: '#fff5c0',
                            onContainer: '#fff5de',
                            container: '#a29742',
                        },
                    }
                }
            }
        }

        const events = [];
        for (let schedule of props.schedules) {
            for (let bin of schedule.bins) {
                for (let binDay of bin.bin_days) {
                    events.push({
                        id: binDay.id,
                        title: bin.bin.name,
                        start: format(new Date(binDay.date), 'yyyy-MM-dd'),
                        end: format(new Date(binDay.date), 'yyyy-MM-dd'),
                        calendar: bin.bin.name,
                    })
                }
            }
        }

        calendarApp = createCalendar({
            selectedDate: format(new Date(), 'yyyy-MM-dd'),
            views: [
                createViewMonthGrid(),
                createViewMonthAgenda(),
            ],
            calendars: calendars,
            events: events,
            isDark: colorMode.value === 'dark',
        })

        shouldShowCalendar.value = true;
    })
}

onMounted(() => {
    createCalendarFromSchedule();
})


</script>

<template>
    <div v-if="shouldShowCalendar">
        <ScheduleXCalendar :calendar-app="calendarApp"/>
    </div>
</template>

<style scoped>

</style>