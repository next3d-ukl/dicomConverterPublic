import SimpleITK as sitk

def get_slice(volume, index, axis=2):
    extract = sitk.ExtractImageFilter()
    
    size = list(volume.GetSize())
    size[axis] = 0 
    extract.SetSize(size)
    
    start_index = [0, 0, 0]
    start_index[axis] = index
    extract.SetIndex(start_index)
    
    slice = extract.Execute(volume)

    # Bilder drehen damit die Anzeige für Menschen nicht geänder wird

    if axis == 0: # Saggital Bild für menschliche anzeige auf den Kopf drehen
        slice = sitk.Flip(slice, [False, True])
    elif axis == 1: # Coronal Bild für menschliche anzeige auf den Kopf drehen
        slice = sitk.Flip(slice, [False, True])
    elif axis == 2:
        slice = sitk.Flip(slice, [False, True])

    return slice
