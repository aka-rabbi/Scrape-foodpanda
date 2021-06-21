

def flatten_data(items_list):
    column_names = ['','A','B','C','D','E','F', 'G']
    cell_range = 'A2:' + 'G' + str(len(items_list)+1)
    
    # new_sheet = file.open("Untitled spreadsheet").add_worksheet('test', 7, len(items_list))
    
    
    flattened_data = []

    for element in items_list:
        for attr in element:
            flattened_data.append(attr)

    return flattened_data, cell_range