from typing import Dict, Any


@staticmethod
def get_meta_from_slice(slice, thickness) -> Dict[str, Any]:
    """
    Extract metadata from a DICOM slice
    """

    def multivalue_to_list(multivalue):
        lst = []
        for element in multivalue:
            lst.append(element)
        return lst

    data_json = {}

    modality = slice.get(0x00080060).value

    if modality != 'PR' and modality != 'SR':
        if modality == 'MR':
            if True:
                rows = slice.get(0x00280010).value
                cols = slice.get(0x00280011).value

                if slice.get(0x00200032).value is None:
                    pos = ''
                else:
                    pos = multivalue_to_list(slice.get(0x00200032).value)
                if slice.get(0x00200037).value is None:
                    direction = ''
                else:
                    direction = multivalue_to_list(slice.get(0x00200037).value)
                spacing = multivalue_to_list(slice.get(0x00280030).value)
                
                data_json = {'rows': rows, 'cols': cols, 'pos': pos, 'direction': direction, 'spacing': spacing,
                             'slice_thickness': thickness}
                print("######################################################")
                print(data_json)
                print("######################################################")
        elif modality == 'CT':
            if True:
                rows = slice.get(0x00280010).value
                cols = slice.get(0x00280011).value

                if slice.get(0x00200032).value is None:
                    pos = ''
                else:
                    pos = multivalue_to_list(slice.get(0x00200032).value)
                if slice.get(0x00200037).value is None:
                    direction = ''
                else:
                    direction = multivalue_to_list(slice.get(0x00200037).value)
                spacing = multivalue_to_list(slice.get(0x00280030).value)

                data_json = {'rows': rows, 'cols': cols, 'pos': pos, 'direction': direction, 'spacing': spacing,
                             'slice_thickness': thickness}

                print("######################################################")
                print(data_json)
                print("######################################################")
    return data_json