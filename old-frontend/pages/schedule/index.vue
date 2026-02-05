<template>
    <LayoutsHome :home-id="homeId">

        <div class="flex w-full justify-end">
            <UButton label="Add Schedule" @click="isScheduleFormOpen = true"/>
        </div>

        <div>

            <UModal v-model="isScheduleFormOpen">
                <AddNewSchedule @updated="loadSchedules" :home-id="homeId"></AddNewSchedule>
            </UModal>

            <UTable :columns="columns" :loading="isLoadingSchedules" :rows="schedules">
                <template #empty-state>
                    <div class="flex flex-col items-center justify-center py-6 gap-3">
                        <span class="italic text-sm">No schedules set yet</span>
                        <UButton label="Add Schedule" @click="isScheduleFormOpen = true"/>
                    </div>
                </template>

                <template #dates-data="{row}">
                <span v-if="row.schedule.start">
                    {{formatDate(row.schedule.start, 'd MMM, yyy')}}
                </span>
                    <span v-else>N/A</span>

                    <span v-if="row.schedule.end">
                    - {{formatDate(row.schedule.end, 'd MMM, yyy')}}
                </span>
                </template>

                <template #repeat_weeks-data="{row}">
                <span v-if="row.schedule.repeat_weeks">
                    Every {{row.schedule.repeat_weeks}} weeks
                </span>
                    <span v-else>Never</span>
                </template>

                <template #next_date-data="{row}">
                <span v-if="row.next_date">
                    <span class="mr-1">{{formatDate(row.next_date, 'd MMM, yyy')}}</span>
                    <span>(in {{daysUntil(row.next_date)}} days)</span>

                </span>
                    <span v-else>Never</span>
                </template>

                <template #bins-data="{row}">
                <span v-if="row.bins">
                    {{row.bins.map(b => b.bin.name).join(', ')}}
                </span>
                    <span v-else>Never</span>
                </template>


                <template #actions-data="{row}">
                    <div class="flex flex-row space-x-2">
                        <UButton @click="recalculateSchedule(row.schedule.id)" color="gray" icon="i-heroicons-arrow-path">Recalculate Schedule</UButton>
                        <!--                    <MakeHomeActive v-if="row.active === false" :home-id="row.id" @activated="loadSchedules"></MakeHomeActive>-->
                        <DeleteSchedule :schedule-id="row.schedule.id" :home-id="homeId" @deleted="loadSchedules"></DeleteSchedule>
                    </div>
                </template>
            </UTable>
        </div>

        <div class="mt-8 mb-8">
            <UDivider></UDivider>
        </div>

        <div>
            <div class="flex w-full justify-end">
                <UButton label="Add Holiday Schedule" @click="isHolidayScheduleFormOpen = true"/>
            </div>

            <UModal v-model="isHolidayScheduleFormOpen">
                <add-new-holiday-schedule @updated="loadReplacementBinDaysAndSchedules" :home-id="homeId">

                </add-new-holiday-schedule>
            </UModal>

            <UTable :columns="binDayReplacementColumns" :loading="isLoadingBinDayReplacements" :rows="binDayReplacements">
                <template #empty-state>
                    <div class="flex flex-col items-center justify-center py-6 gap-3">
                        <span class="italic text-sm">No date replacements set yet</span>
                        <UButton label="Add Holiday Schedule" @click="isHolidayScheduleFormOpen = true"/>
                    </div>
                </template>

                <template #replace-data="{row}">
                <span v-if="row.replace">
                    {{formatDate(row.replace, 'd MMM, yyy')}}
                </span>
                    <span v-else>N/A</span>
                </template>

                <template #with-data="{row}">
                <span v-if="row.with">
                    {{formatDate(row.with, 'd MMM, yyy')}}
                </span>
                    <span v-else>N/A</span>
                </template>

                <template #actions-data="{row}">
                    <div class="flex flex-row space-x-2">
                        <DeleteBinReplacementDay :replacement-bin-day-id="row.id" :home-id="homeId" @deleted="loadReplacementBinDaysAndSchedules"></DeleteBinReplacementDay>
                    </div>
                </template>
            </UTable>
        </div>

        <div class="mt-8 mb-8">
            <UDivider></UDivider>
        </div>

        <ClientOnly>
            <div class="mt-8" v-if="schedules.length > 0">
                <show-calendar :schedules="schedules"></show-calendar>
            </div>
        </ClientOnly>


    </LayoutsHome>

</template>

<script lang="ts" setup>
import { format } from 'date-fns'

const route = useRoute();

const homeId = Number(route.params.id);

const isScheduleFormOpen = ref<boolean>(false)

const isHolidayScheduleFormOpen = ref<boolean>(false)

const formatDate = (date: string) => {
    return format(new Date(date), 'd MMM, yyy')
}

const daysUntil = (date: string) => {
    const now = new Date()
    const target = new Date(date)
    const diff = target.getTime() - now.getTime()
    return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

const columns = [
    {
        label: 'Dates',
        key: 'dates'
    },
    {
        label: 'Repeat',
        key: 'repeat_weeks'
    },
    {
        label: 'Bins',
        key: 'bins'
    },
    {
        label: 'Next Date',
        key: 'next_date'
    },
    {
        key: 'actions'
    }
]

const schedules = ref<Schedule[]>([]);

const isLoadingSchedules = ref<boolean>(true)

const loadSchedules = () => {
    isLoadingSchedules.value = true
    isScheduleFormOpen.value = false
    $fetch('/api/home/' + homeId + '/schedule')
        .then((response) => {
            schedules.value = response.schedules
        })
        .catch((error) => {
            console.error(error)
        })
        .finally(() => {
            isLoadingSchedules.value = false
        })
}

onMounted(() => {
    loadSchedules();
})

const recalculateSchedule = (scheduleId: number) => {
    isLoadingSchedules.value = true
    $fetch(`/api/home/${homeId}/schedule/${scheduleId}/recalculate`, {
        method: 'POST',
    })
        .then(() => {
            loadSchedules()
        })
        .catch((error) => {
            console.error(error)
        })
        .finally(() => {
            isLoadingSchedules.value = false
        })
}

const binDayReplacements = ref<BinDayReplacement[]>([]);

const isLoadingBinDayReplacements = ref<boolean>(true)

const loadReplacementBinDays = () => {
    isLoadingBinDayReplacements.value = true
    isHolidayScheduleFormOpen.value = false
    $fetch('/api/home/' + homeId + '/bin-day-replacement')
        .then((response) => {
            binDayReplacements.value = response.bin_day_replacements
        })
        .catch((error) => {
            console.error(error)
        })
        .finally(() => {
            isLoadingBinDayReplacements.value = false
        })
}

onMounted(() => {
    loadReplacementBinDays();
})


const binDayReplacementColumns = [
    {
        label: 'Usual collection date',
        key: 'replace'
    },
    {
        label: 'New collection date',
        key: 'with'
    },
    {
        key: 'actions'
    }
]

const loadReplacementBinDaysAndSchedules = () => {
    loadReplacementBinDays();
    loadSchedules();
}
</script>