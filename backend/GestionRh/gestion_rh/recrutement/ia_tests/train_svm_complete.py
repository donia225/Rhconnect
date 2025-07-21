
import os
import pandas as pd
import joblib
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# 1️⃣ Charger le dataset préparé
df = pd.read_csv("dataset/prepared_dataset.csv")
X = df.drop(columns=["label"])
y = df["label"]
print("Distribution des classes :")
print(y.value_counts())


# 2️⃣ Diviser le dataset en train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 3️⃣ Entraînement du modèle SVM par défaut
svm = SVC()
svm.fit(X_train, y_train)
y_pred = svm.predict(X_test)

# 4️⃣ Évaluer les performances
print("🔍 Évaluation SVM (Modèle par défaut)")
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Precision:", precision_score(y_test, y_pred))
print("Recall:", recall_score(y_test, y_pred))
print("F1 Score:", f1_score(y_test, y_pred))

# 5️⃣ Cross-validation
scores = cross_val_score(svm, X, y, cv=5, scoring="f1")
print("🎯 Moyenne F1 (cross-val):", scores.mean())

# 6️⃣ Réglage des hyper-paramètres
print("🔧 Tuning des hyperparamètres...")
param_grid = {
    "C": [0.1, 1, 10],
    "kernel": ["linear", "rbf"],
    "gamma": ["scale", "auto"]
}
grid = GridSearchCV(SVC(), param_grid, cv=5, scoring="f1")
grid.fit(X_train, y_train)

# 7️⃣ Évaluer le meilleur modèle
best_model = grid.best_estimator_
best_pred = best_model.predict(X_test)

print("✅ Meilleur modèle après tuning :")
print("Meilleurs paramètres:", grid.best_params_)
print("Accuracy:", accuracy_score(y_test, best_pred))
print("Precision:", precision_score(y_test, best_pred))
print("Recall:", recall_score(y_test, best_pred))
print("F1 Score:", f1_score(y_test, best_pred))

# 8️⃣ Sauvegarder le meilleur modèle
os.makedirs("ml_model", exist_ok=True)
joblib.dump(best_model, "ml_model/best_svm_model.joblib")
print("💾 Modèle sauvegardé sous ml_model/best_svm_model.joblib")
