import pandas as pd

# Chargement du dataset
df = pd.read_csv("dataset/prepared_dataset.csv")

# Affichage du nombre de lignes et des premières lignes du dataset
print("📊 Nombre d'échantillons :", len(df))
print("🧾 Aperçu des données :")
print(df.head())
print("📊 Distribution des classes :")
print(df["label"].value_counts())

