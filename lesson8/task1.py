#%% Change working directory from the workspace root to the ipynb file location. Turn this addition off with the DataScience.changeDirOnImportExport setting
import os
try:
	os.chdir(os.path.join(os.getcwd(), '/'))
	print(os.getcwd())
except:
	pass

#%%
import numpy as np
import pandas as pd

#%% [markdown]
# Задача 1 

#%%
from sklearn.datasets import load_boston

#%%
boston = load_boston()
X = pd.DataFrame(boston.data, columns=boston.feature_names)
y = pd.DataFrame(boston.target, columns=['price'])

#%%
X.head()

#%%
y.head()

#%%
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

#%%
from sklearn.linear_model import LinearRegression
lr = LinearRegression()
lr.fit(X_train, y_train)
y_pred = lr.predict(X_test)
y_pred[:5]

#%%
from sklearn.metrics import r2_score
r2_score(y_test, y_pred)

#%% [markdown]
# Задача 2


#%%
from sklearn.ensemble import RandomForestRegressor
model = RandomForestRegressor(n_estimators=1000, max_depth=12, random_state=42, n_jobs=8)

#%%
model.fit(X_train, y_train.values[:,0])
y_forest_pred = model.predict(X_test)
y_forest_pred[:5]

#%%
r2_score(y_test, y_forest_pred)

#%% [markdown]
# Модель с деревьми работает лучше


#%% [markdown]
# Задание 3*


#%%
importances = model.feature_importances_
np.sum(importances)

#%%
indx = np.argsort(importances)
indx = indx[::-1]

#%%
print(f"{boston.feature_names[indx[0]]} важность {importances[indx[0]]}")
print(f"{boston.feature_names[indx[1]]} важность {importances[indx[1]]}")

#%%
