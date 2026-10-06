import pandas as pd

# Data inlezen 
df_projecturen_minsc = pd.read_csv("Data_1/projecthours (misc).csv")
df_projecturen_med1 = pd.read_csv("Data_1/projecthours (med) - wk 1 tm 12.csv")
df_projecturen_med2 = pd.read_csv("Data_1/projecthours (med) - wk 13 to 32.csv")
df_projecturen_aut1 = pd.read_csv("Data_1/projecthours (aut) - wk 1 tm 31.csv")
df_projecturen_ret = pd.read_csv("Data_1/projecthours (3 retail projects).csv")
df_projecturen_Claire = pd.read_csv("Data_1/projecthours (Claire on AUT00560058).csv") # zit in de lijst
df_projecturen_Kenneth = pd.read_csv("Data_1/projecthours (Kenneth on AUT).csv") # zit in de lijst

# Uitleg over wat iedere rij betekent staat er ook in 
Extra_werknemers1 = pd.read_csv('Data_1/EXPORT_20250831 - Extra Employees.txt', sep=";")
Extra_werknemers2 = pd.read_csv('Data_1/EXPORT_20240907 - Extra Employees.txt', sep=";")
Werknemers_Tilburg = pd.read_csv('Data_1/Employees (Tilburg).csv', sep=';')
Werknemers_Management = pd.read_csv('Data_1/Employees (management).csv')

# Data samenvoegen
projecturen = pd.concat([df_projecturen_minsc, df_projecturen_med1, 
                df_projecturen_med2,df_projecturen_aut1,
                df_projecturen_ret ], ignore_index=True)

Werknemers = pd.concat([Extra_werknemers1, Extra_werknemers2, Werknemers_Tilburg,Werknemers_Management], ignore_index=True)

Dubbele1 = Werknemers[Werknemers.duplicated(keep=False)] # 0 dubbele rijen 
#print(len(Dubbele1))

Dubbele2 = projecturen[projecturen.duplicated(keep=False)] # 318 dubbele rijen 
#print(len(Dubbele2))
projecturen = projecturen.drop_duplicates(keep="first")

#print(len(df_projecturen_med2[df_projecturen_med2.duplicated(keep=False)])) #6 dubbele rijen

# Projecturen exporteren
projecturen.to_excel(
    "export_projecturen.xlsx",
    index=False)

# Werknemers exporteren
Werknemers.to_excel(
    "export_werknemers.xlsx",
    index=False)

print("Beide Excel-bestanden zijn opgeslagen in Data_1")


