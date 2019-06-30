#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#%%
from pylab import rcParams
get_ipython().run_line_magic('matplotlib', 'inline')
get_ipython().run_line_magic('config', "InlineBackend.figure_format = 'svg'")
rcParams['figure.figsize'] = 6, 4.5

#%%
from sklearn.datasets import load_boston

#%%
boston = load_boston()
feature_names = boston.feature_names
X = pd.DataFrame(boston.data, columns=boston.feature_names)
y = pd.DataFrame(boston.target, columns=['price'])

#%%
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#%%
X_train.head()

#%%
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()


#%%
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
X_train_scaled = pd.DataFrame(X_train_scaled, columns=feature_names)
X_test_scaled = pd.DataFrame(X_test_scaled, columns=feature_names)

#%%
X_train_scaled.head()

#%%
from sklearn.manifold import TSNE

#%%
tsne = TSNE(n_components=2, learning_rate=250, random_state=42)

#%%
X_train_tsne = tsne.fit_transform(X_train_scaled)

#%%
X_train_tsne

#%%
plt.scatter(X_train_tsne[:, 0], X_train_tsne[:, 1])
plt.show()

#%%
from sklearn.cluster import KMeans

#%%
kmeans = KMeans(n_clusters=3, max_iter = 100, random_state=42)

#%%
labels_train = kmeans.fit_predict(X_train_scaled)

#%%
pd.value_counts(labels_train)

#%%
plt.scatter(X_train_tsne[:, 0], X_train_tsne[:, 1], c=labels_train)
plt.text(-27, -5, 'Кластер 0')
plt.text(15, -7, 'Кластер 1')
plt.text(0, 25, 'Кластер 2')
#%%

X_train.loc[labels_train==0, 'CRIM'].mean()

#%%
X_train.loc[labels_train==1, 'CRIM'].mean()

#%%
X_train.loc[labels_train==2, 'CRIM'].mean()

#%%
y_train.loc[labels_train==0, 'price'].mean()

#%%
y_train.loc[labels_train==1, 'price'].mean()
#%%
y_train.loc[labels_train==2, 'price'].mean()

