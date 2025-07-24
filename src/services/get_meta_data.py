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
            if 'DERIVED' in slice.get(0x00080008).value:
                try:
                    spacing = multivalue_to_list(slice.get(0x00280030).value)
                    data_json = {'spacing': spacing}
                except:
                    pass
            else:
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
        elif modality == 'CT':
            if 'DERIVED' in slice.get(0x00080008).value:
                try:
                    spacing = multivalue_to_list(slice.get(0x00280030).value)
                    data_json = {'spacing': spacing}
                except:
                    pass
            else:
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
    return data_json