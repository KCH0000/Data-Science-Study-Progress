#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import Normalizer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score


#%%
from pylab import rcParams
get_ipython().run_line_magic('matplotlib', 'inline')
get_ipython().run_line_magic('config', "InlineBackend.figure_format = 'svg'")
rcParams['figure.figsize'] = 8, 7

#%%
train = pd.read_csv('final/data/train.csv')

#%% Удаляем лишние стобцы
train = train.drop(['Healthcare_1'], axis=1)

#%% Удаляем явно ошибочные записи
train = train.loc[~(train['Id'] == train['Ecology_2'])]

#%%  [markdown] 
# Поля Flor и HouseFloor

#%% Убираем очень высокие здания.
train.loc[train['HouseFloor'] > 50, ['HouseFloor']] = train['HouseFloor'].mean().astype('int')

#%% Убираем очень большие этаж.
train.loc[train['Floor'] > 50 , ['Floor']] = train['Floor'].mean().astype('int')

#%% Убираем этажность здания, где этаже больше здания.
train.loc[train['Floor'] > train['HouseFloor'], ['HouseFloor']] = train['Floor']

#%% Cоставим признак, который указывает на первый или последний этаж
train['frs_lst_floor'] = (train['Floor'] == train['HouseFloor']) | (train['Floor'] <= 1)
train['frs_lst_floor'] = train['frs_lst_floor'].astype('int')

#%% [markdown]
# Поле HouseYear

#%% fix неправильной записи
train.loc[train['HouseYear'] == 20052011, ['HouseYear']] = 2005

#%% Заменяем слишком большие и слишком маленькие года домов на средние по району
train.loc[~train['HouseYear'].between(1800, 2030), ['HouseYear']] = train.loc[train['HouseYear'].between(1800, 2030), :].groupby(['DistrictId'])['HouseYear'].mean().astype('int32')

#%% Определим возраст района
dist_mean_year = train.groupby(['DistrictId'])[['HouseYear']].mean().astype('int32').reset_index().rename(columns={'HouseYear': 'Dist_mean_year'})
train = train.merge(dist_mean_year, on=('DistrictId'), how='left')

#%% Заполняем пустые года
train.loc[train['HouseYear'].isna(), ['HouseYear']] = train['Dist_mean_year']

#%% Новый признак - исторический дом
train['Historical_House'] = (train['HouseYear'] < 1930).astype('int32')

#%% Новый признак - военные дома
train['War_House'] = (train['HouseYear'].between(1929, 1947)).astype('int32')

#%% Новый признак - дом в процессе строителства или сдачи
train['Not_Finish_House'] = (train['HouseYear'] >= 2018).astype('int32')

#%% [markdown]
# Поля LifeSquare Square Rooms

#%% Устновка общей площади, которая меньше жилой
train.loc[train['LifeSquare'] > train['Square'], ['Square']] = train['LifeSquare']

#%% Редактирование слишком маленьких площадей
train.loc[train['Square'] < 15, ['Square', 'LifeSquare']] = train[['Square', 'LifeSquare']] * 10

#%% Уделание завышенных площадей
train = train.loc[train['Square'].between(15, 700)]

#%% Средняя комната в районе в домах одного года постройки
square_mean_dist_rooms = train.loc[train['Rooms'] != 0].groupby(['DistrictId', 'Rooms', 'HouseYear'])[['Square']].mean().reset_index().rename(columns={'Square': 'Square_mean_dist_rooms'})
square_mean_dist_rooms['Room_mean_sq'] = square_mean_dist_rooms['Square_mean_dist_rooms'] / square_mean_dist_rooms['Rooms']
square_mean_dist_rooms = square_mean_dist_rooms.drop(['Rooms', 'Square_mean_dist_rooms'], axis=1)
square_mean_dist_rooms = square_mean_dist_rooms.groupby(['DistrictId', 'HouseYear'])['Room_mean_sq'].mean().reset_index()
train = train.merge(square_mean_dist_rooms, on=['DistrictId', 'HouseYear'], how='left')

#%% Выставляем 	Room_mean_sq у строк, которые не заполнились
train.loc[train['Room_mean_sq'].isna(), ['Room_mean_sq']] = train['Room_mean_sq'].mean()

#%% Расчет количаства комнат 
train.loc[train['Rooms'] == 0, ['Rooms']] = (train['Square'] / train['Room_mean_sq']).astype('int32')
train.loc[train['Rooms'] > 6 , ['Rooms']] = (train['Square'] / train['Room_mean_sq']).astype('int32')
train.loc[train['Rooms'] == 0, ['Rooms']] = 1

#%% Ввод показателя Square^2
train['Square_2'] = train['Square'] ** 2

#%% Ввод новых параметров. Нормальное кол-во комнат, Нормальнаый год
train[['N_Rooms', 'N_HouseYear']] = train[['Rooms', 'HouseYear']]
train.loc[train['N_Rooms'] > 3, ['N_Rooms']] = 4
train.loc[train['Historical_House'] == 1, ['N_HouseYear']] = 1910
train['N_HouseYear']  -= train['N_HouseYear'] % 10

#%% Ввод показателя для финасовой составляющей района
dist_room_mean_price = train.groupby(['DistrictId', 'N_Rooms', 'N_HouseYear'])['Price'].mean().reset_index().rename(columns={'Price':'Mean_Dist_Price'})
train = train.merge(dist_room_mean_price, on=['DistrictId', 'N_Rooms', 'N_HouseYear'], how='left')

#%% [markdown]
# KitchenSquare и LifeSquare учитывать в расчетах не будем в виду серьезных допущений

#%% [markdown]
# Поле эколоджи Ecology_1 используем как есть

#%% [markdown]
# Поле эколоджи Ecology_2 Ecology_3  Shops_2 перевести в dummies
train = pd.get_dummies(train)

#%% [markdown] 
# Обучение

#%% Поля для участия в обучении
fts = [
        # 'Id',
        # 'DistrictId',
        # 'Rooms',
        # 'Square',
        'Square_2',
        # 'LifeSquare',
        # 'KitchenSquare',
        'Floor',
        'HouseFloor',
        'HouseYear',
        'Ecology_1',
        'Social_1',
        'Social_2',
        'Social_3',
        'Helthcare_2',
        'Shops_1',
        # 'Price',
        'frs_lst_floor',
        'Dist_mean_year',
        'Historical_House',
        'War_House',
        'Not_Finish_House',
        'Room_mean_sq',
        'Ecology_2_A',
        'Ecology_2_B',
        'Ecology_3_A',
        'Ecology_3_B',
        'Shops_2_A',
        'Shops_2_B',
        'Mean_Dist_Price',
        # 'N_Rooms',
        # 'N_HouseYear'
]

#%% Получение тестового и валидационного датасетов
X = train[fts]
y = train['Price']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# #%% Нормализация данных
# scaler = StandardScaler()
# X_train_scaled = scaler.fit_transform(X_train)
# X_test_scaled = scaler.transform(X_test)
# X_train_scaled = pd.DataFrame(X_train_scaled, columns=fts)
# X_test_scaled = pd.DataFrame(X_test_scaled, columns=fts)

# #%% Обучение RF на нормаливанных данных
# model = RandomForestRegressor(n_estimators=2000,  max_depth=15, random_state=42, n_jobs=8)
# model.fit(X_train_scaled, y_train)
# train_pred = model.predict(X_train_scaled)
# r2_score(y_train, train_pred)

# #%% Проверка на нормализованных данных
# test_pred = model.predict(X_test_scaled)
# r2_score(y_test, test_pred)

#%% Подбор параметров на стоке
# score_train = 0
# score_test = 0
# best_dep = 0
# for i in range(100, 2000, 200):
#         model = RandomForestRegressor(n_estimators=i,  max_depth=12, random_state=42, n_jobs=8)
#         model.fit(X_train, y_train)
#         train_pred = model.predict(X_train)
#         r2_train = r2_score(y_train, train_pred)
#         test_pred = model.predict(X_test)
#         r2_test = r2_score(y_test, test_pred)
#         if r2_test > score_test:
#                 score_test = r2_test
#                 score_train = r2_train
#                 best_dep = i
# print('Лучшее {} при dep = {} (train {})'.format(score_test, best_dep, score_train))

#%% Расчет на стоке
model = RandomForestRegressor(n_estimators=700,  max_depth=14, random_state=42, n_jobs=8)
model.fit(X_train, y_train)
train_pred = model.predict(X_train)
r2_train = r2_score(y_train, train_pred)
test_pred = model.predict(X_test)
r2_test = r2_score(y_test, test_pred)
print('r2 тест: {}, r2 трайн: {}'.format(r2_test, r2_train))




#0----------------------------------------------------------------------------------------


#%% [markdown] 
# Обработка test.csv

#%%
test = pd.read_csv('final/data/test.csv')
test.describe()

#%% Удаляем лишние стобцы
test = test.drop(['Healthcare_1'], axis=1)

#%% Проверяем могут ли быть потенциально ошибочные данные
test.loc[test['Id'] == test['Helthcare_2']]

#%%  [markdown] 
# Поля Flor и HouseFloor

#%% Убираем очень высокие здания.
test.loc[test['HouseFloor'] > 50, ['HouseFloor']] = test['HouseFloor'].mean().astype('int')

#%% Убираем этажность здания, где этаже больше здания.
test.loc[test['Floor'] > test['HouseFloor'], ['HouseFloor']] = test['Floor']

#%% Cоставим признак, который указывает на первый или последний этаж
test['frs_lst_floor'] = (test['Floor'] == test['HouseFloor']) | (test['Floor'] <= 1)
test['frs_lst_floor'] = test['frs_lst_floor'].astype('int')

#%% [markdown]
# Поле HouseYear

#%% Заменяем слишком большие и слишком маленькие года домов на средние по району
test.loc[~test['HouseYear'].between(1800, 2030), ['HouseYear']] = test.loc[test['HouseYear'].between(1800, 2030), :].groupby(['DistrictId'])['HouseYear'].mean().astype('int32')

#%% Определим возраст района
dist_mean_year = test.groupby(['DistrictId'])[['HouseYear']].mean().astype('int32').reset_index().rename(columns={'HouseYear': 'Dist_mean_year'})
test = test.merge(dist_mean_year, on=('DistrictId'), how='left')

#%% Заполняем пустые года
test.loc[test['HouseYear'].isna(), ['HouseYear']] = test['Dist_mean_year']

#%% Новый признак - исторический дом
test['Historical_House'] = (test['HouseYear'] < 1930).astype('int32')

#%% Новый признак - военные дома
test['War_House'] = (test['HouseYear'].between(1929, 1947)).astype('int32')

#%% Новый признак - дом в процессе строителства или сдачи
test['Not_Finish_House'] = (test['HouseYear'] >= 2018).astype('int32')

#%% [markdown]
# Поля LifeSquare Square Rooms

#%% Устновка общей площади, которая меньше жилой
test.loc[test['LifeSquare'] > test['Square'], ['Square']] = test['LifeSquare']

#%% Редактирование слишком маленьких площадей
test.loc[test['Square'] < 13, ['Square', 'LifeSquare']] = test[['Square', 'LifeSquare']] * 10


#%% Средняя комната в районе в домах одного года постройки
square_mean_dist_rooms = test.loc[test['Rooms'] != 0].groupby(['DistrictId', 'Rooms', 'HouseYear'])[['Square']].mean().reset_index().rename(columns={'Square': 'Square_mean_dist_rooms'})
square_mean_dist_rooms['Room_mean_sq'] = square_mean_dist_rooms['Square_mean_dist_rooms'] / square_mean_dist_rooms['Rooms']
square_mean_dist_rooms = square_mean_dist_rooms.drop(['Rooms', 'Square_mean_dist_rooms'], axis=1)
square_mean_dist_rooms = square_mean_dist_rooms.groupby(['DistrictId', 'HouseYear'])['Room_mean_sq'].mean().reset_index()
test = test.merge(square_mean_dist_rooms, on=['DistrictId', 'HouseYear'], how='left')

#%% Выставляем 	Room_mean_sq у строк, которые не заполнились
test.loc[test['Room_mean_sq'].isna(), ['Room_mean_sq']] = test['Room_mean_sq'].mean()

#%% Расчет количаства комнат 
test.loc[test['Rooms'] == 0, ['Rooms']] = (test['Square'] / test['Room_mean_sq']).astype('int32')
test.loc[test['Rooms'] > 6 , ['Rooms']] = (test['Square'] / test['Room_mean_sq']).astype('int32')
test.loc[test['Rooms'] == 0, ['Rooms']] = 1

#%% Ввод показателя Square^2
test['Square_2'] = test['Square'] ** 2

#%% Ввод новых параметров. Нормальное кол-во комнат, Нормальнаый год
test[['N_Rooms', 'N_HouseYear']] = test[['Rooms', 'HouseYear']]
test.loc[test['N_Rooms'] > 3, ['N_Rooms']] = 4
test.loc[test['Historical_House'] == 1, ['N_HouseYear']] = 1910
test['N_HouseYear']  -= test['N_HouseYear'] % 10

#%% Ввод показателя для финасовой составляющей района, максимальная точность
dist_room_mean_price = train.groupby(['DistrictId', 'N_Rooms', 'N_HouseYear'])['Price'].mean().reset_index().rename(columns={'Price':'Mean_Dist_Price'})
test = test.merge(dist_room_mean_price, on=['DistrictId', 'N_Rooms', 'N_HouseYear'], how='left')

#%%  Mean_Dist_Price из точной стоимости м2
price_dist_m2_mean = test.loc[~test['Mean_Dist_Price'].isna()].groupby(['DistrictId','N_HouseYear'])[['Square','Mean_Dist_Price']].mean().reset_index().rename(columns={'Mean_Dist_Price':'Mean_Dist_Price_2'})
price_dist_m2_mean['Price_mean_m2'] = price_dist_m2_mean['Mean_Dist_Price_2'] / price_dist_m2_mean['Square']
price_dist_m2_mean = price_dist_m2_mean.drop(['Mean_Dist_Price_2', 'Square'], axis=1)
test = test.merge(price_dist_m2_mean, on=['DistrictId', 'N_HouseYear'], how='left')
test.loc[test['Mean_Dist_Price'].isna(), ['Mean_Dist_Price']] = test['Price_mean_m2'] * test['Square']
test = test.drop(['Price_mean_m2'], axis=1)

#%% Mean_Dist_Price из неточной стоимости м2
price_dist_m2_mean = test.loc[~test['Mean_Dist_Price'].isna()].groupby(['DistrictId'])[['Square','Mean_Dist_Price']].mean().reset_index().rename(columns={'Mean_Dist_Price':'Mean_Dist_Price_2'})
price_dist_m2_mean['Price_mean_m2'] = price_dist_m2_mean['Mean_Dist_Price_2'] / price_dist_m2_mean['Square']
price_dist_m2_mean = price_dist_m2_mean.drop(['Mean_Dist_Price_2', 'Square'], axis=1)
test = test.merge(price_dist_m2_mean, on=['DistrictId'], how='left')
test.loc[test['Mean_Dist_Price'].isna(), ['Mean_Dist_Price']] = test['Price_mean_m2'] * test['Square']

#%% Mean_Dist_Price дозаполнение средним показателем.
test.loc[test['Mean_Dist_Price'].isna(), ['Mean_Dist_Price']] = test['Price_mean_m2'].mean() * test['Square']

#%% Создаем dummies
test = pd.get_dummies(test)

#%% Обучаем модель на тестовых данных
model = RandomForestRegressor(n_estimators=700,  max_depth=14, random_state=42, n_jobs=8)
model.fit(train[fts], train['Price'])

#%% Предстказываем
price_pred = model.predict(test[fts])

#%% Сохранение результата в поле Price
test['Price'] = price_pred

#%%
test[['Id', 'Price']].to_csv('KSidorov_predictions.csv', index=None)

#%%
