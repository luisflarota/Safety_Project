from hashlib import new
import pandas as pd
import numpy as np

data_accidents = pd.read_excel('01_Accidents_Fill.xlsx')

columns = data_accidents.columns

new_list = []
for row in np.array(data_accidents):
    description = row[4].split()
    new_description = sorted(description)
    new_description = ' '.join(new_description)
    row[4] = new_description
    new_list.append(row)

new_data = pd.DataFrame(new_list, columns = columns)
new_data.to_excel('01_Accidents_Fill_c.xlsx')
