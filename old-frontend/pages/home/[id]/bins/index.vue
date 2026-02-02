<template>
    <LayoutsHome :home-id="homeId">
        <div class="flex flex-row w-full justify-end mb-2">
            <UButton color="gray" icon="i-heroicons-arrow-path" @click="loadBinOptions" :loading="isLoadingBinOptions">Load bin options from council</UButton>
        </div>
        <div class="flex flex-row w-full justify-end mb-2" v-if="isLoadingBinOptions">
              <UProgress animation="carousel" />
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4" v-show="!isLoadingBins">
            <div v-for="position in noOfVisibleBins">
                <BinSetup :key="('position:' + ((bins ?? []).find(b => b.position === position)?.id ?? 'Empty'))" :home-id="homeId" :position="position" :options="binOptions"
                          :bin="(bins ?? []).find(b => b.position === position) || null" @updated="loadBins">

                </BinSetup>
            </div>


<!--            <BinSetup :key="2" :home-id="homeId" :position="2" :options="binOptions" :bin="(bins ?? []).find(b => b.position === 2) || null" @updated="loadBins">-->

<!--            </BinSetup>-->

<!--            <BinSetup :key="3" :home-id="homeId" :position="3" :options="binOptions" :bin="(bins ?? []).find(b => b.position === 3) || null" @updated="loadBins">-->

<!--            </BinSetup>-->

<!--            <BinSetup :key="4" :home-id="homeId" :position="4" :options="binOptions" :bin="(bins ?? []).find(b => b.position === 4) || null" @updated="loadBins">-->

<!--            </BinSetup>-->

            <div class="h-full min-h-24 flex justify-center items-center" v-if="noOfVisibleBins < maxBins">
                <UButton icon="i-heroicons-plus" @click="addBin">Add Bin</UButton>
            </div>
        </div>
    </LayoutsHome>
</template>

<script lang="ts" setup>
import type {Bin} from "~/server/utils/drizzle";

const route = useRoute();

const homeId = Number(route.params.id);

const isLoadingBins = ref<boolean>(true)

const bins = ref<Bin[]>([])

const maxBins = 7;

const noOfVisibleBins = ref<number>(1);

const addBin = () => {
    if(noOfVisibleBins.value < maxBins) {
        noOfVisibleBins.value++;
    }
}

const loadBins = () => {
    isLoadingBins.value = true
    $fetch(`/api/home/${homeId}/bins`)
        .then((response) => {
            let newBins = response.bins || [];

            let newNoOfVisibleBins = Math.max(...newBins.map(b => b.position), 1)

            if(newNoOfVisibleBins > noOfVisibleBins.value) {
                noOfVisibleBins.value = newNoOfVisibleBins
            }

            if(!Array.isArray(response.bins)) {
                bins.value = [response.bins]
            } else {
                bins.value = response.bins || [];
            }

        })
        .catch((error) => {
            console.error(error)
        })
        .finally(() => {
            isLoadingBins.value = false
        })
}

const isLoadingBinOptions = ref<boolean>(false)
const binOptions = ref<string[]>([])
const loadBinOptions = () => {
    isLoadingBinOptions.value = true
    $fetch(`/api/home/${homeId}/bins/options`)
        .then((response) => {
            binOptions.value = response.options || []
        })
        .catch((error) => {
            console.error(error)
        })
        .finally(() => {
            isLoadingBinOptions.value = false
        })
}

onMounted(() => {
    loadBins();
})

</script>