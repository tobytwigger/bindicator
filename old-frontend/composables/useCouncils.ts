import {computed} from "vue";
import MiltonKeynes from "~/components/councils/MiltonKeynes.vue";
import Buckinghamshire from "~/components/councils/Buckinghamshire.vue";
import GenericCouncilComponent from "~/components/councils/GenericCouncilComponent.vue";

export const useCouncils = () => {
    const councils = [
        new MiltonKeynesCouncil(),
        new BuckinghamshireCouncil(),
        new TeignbridgeCouncil()
    ];

    const councilSelectSchema = computed(() => {
        return [{value: null, label: 'Other'}]
            .concat(
                councils.map(council => {
                    return {
                        value: council.key,
                        label: council.name
                    }
                })
            );
    });

    const councilKeys = computed<Array<string>>(() => {
        return councils.map(council => council.key);
    });

    return {
        councils,
        councilSelectSchema,
        councilKeys
    }
}

// Define the council properties available in an enum
export enum CouncilProperties {
    HouseNumber = 'house_number',
    Postcode = 'postcode',
    Uprn = 'uprn',
}

export abstract class Council {
    abstract key: string;
    abstract name: string;
    component = GenericCouncilComponent;
    abstract properties: CouncilProperties[]
}

class MiltonKeynesCouncil extends Council {
    key = 'MiltonKeynesCityCouncil';
    name = 'Milton Keynes City Council';
    properties = [CouncilProperties.Uprn];
}

class BuckinghamshireCouncil extends Council {
    key = 'BuckinghamshireCouncil';
    name = 'Buckinghamshire Council';
    properties = [CouncilProperties.HouseNumber, CouncilProperties.Postcode];
}

class TeignbridgeCouncil extends Council {
    key = 'TeignbridgeCouncil';
    name = 'Teignbridge Council';
    properties = [CouncilProperties.Uprn];
}