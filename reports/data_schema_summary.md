# Data Schema Summary

This report is generated from local raw CSV files under `data/raw/`.
Raw data files are read only and are not modified by the loader.

## Required File Check

| file | column_count | first_columns |
| --- | --- | --- |
| application_train.csv | 122 | SK_ID_CURR, TARGET, NAME_CONTRACT_TYPE, CODE_GENDER, FLAG_OWN_CAR, FLAG_OWN_REALTY, CNT_CHILDREN, AMT_INCOME_TOTAL |
| HomeCredit_columns_description.csv | 5 | Unnamed: 0, Table, Row, Description, Special |
| bureau.csv | 17 | SK_ID_CURR, SK_ID_BUREAU, CREDIT_ACTIVE, CREDIT_CURRENCY, DAYS_CREDIT, CREDIT_DAY_OVERDUE, DAYS_CREDIT_ENDDATE, DAYS_ENDDATE_FACT |
| bureau_balance.csv | 3 | SK_ID_BUREAU, MONTHS_BALANCE, STATUS |
| previous_application.csv | 37 | SK_ID_PREV, SK_ID_CURR, NAME_CONTRACT_TYPE, AMT_ANNUITY, AMT_APPLICATION, AMT_CREDIT, AMT_DOWN_PAYMENT, AMT_GOODS_PRICE |
| installments_payments.csv | 8 | SK_ID_PREV, SK_ID_CURR, NUM_INSTALMENT_VERSION, NUM_INSTALMENT_NUMBER, DAYS_INSTALMENT, DAYS_ENTRY_PAYMENT, AMT_INSTALMENT, AMT_PAYMENT |
| POS_CASH_balance.csv | 8 | SK_ID_PREV, SK_ID_CURR, MONTHS_BALANCE, CNT_INSTALMENT, CNT_INSTALMENT_FUTURE, NAME_CONTRACT_STATUS, SK_DPD, SK_DPD_DEF |
| credit_card_balance.csv | 23 | SK_ID_PREV, SK_ID_CURR, MONTHS_BALANCE, AMT_BALANCE, AMT_CREDIT_LIMIT_ACTUAL, AMT_DRAWINGS_ATM_CURRENT, AMT_DRAWINGS_CURRENT, AMT_DRAWINGS_OTHER_CURRENT |

## Base Table

- Base table: `application_train.csv`
- Shape: `307,511` rows x `122` columns
- Target column detected: `TARGET`

## Target Distribution

| TARGET | count | percent |
| --- | --- | --- |
| 0 | 282686 | 91.93 |
| 1 | 24825 | 8.07 |

## Data Type Summary

| dtype | column_count |
| --- | --- |
| float64 | 65 |
| int64 | 41 |
| str | 16 |

## Top Missing-Value Columns

| column | missing_count | missing_percent | dtype |
| --- | --- | --- | --- |
| COMMONAREA_AVG | 214865 | 69.87 | float64 |
| COMMONAREA_MEDI | 214865 | 69.87 | float64 |
| COMMONAREA_MODE | 214865 | 69.87 | float64 |
| NONLIVINGAPARTMENTS_AVG | 213514 | 69.43 | float64 |
| NONLIVINGAPARTMENTS_MEDI | 213514 | 69.43 | float64 |
| NONLIVINGAPARTMENTS_MODE | 213514 | 69.43 | float64 |
| FONDKAPREMONT_MODE | 210295 | 68.39 | str |
| LIVINGAPARTMENTS_AVG | 210199 | 68.35 | float64 |
| LIVINGAPARTMENTS_MEDI | 210199 | 68.35 | float64 |
| LIVINGAPARTMENTS_MODE | 210199 | 68.35 | float64 |
| FLOORSMIN_AVG | 208642 | 67.85 | float64 |
| FLOORSMIN_MEDI | 208642 | 67.85 | float64 |
| FLOORSMIN_MODE | 208642 | 67.85 | float64 |
| YEARS_BUILD_AVG | 204488 | 66.5 | float64 |
| YEARS_BUILD_MEDI | 204488 | 66.5 | float64 |
| YEARS_BUILD_MODE | 204488 | 66.5 | float64 |
| OWN_CAR_AGE | 202929 | 65.99 | float64 |
| LANDAREA_AVG | 182590 | 59.38 | float64 |
| LANDAREA_MEDI | 182590 | 59.38 | float64 |
| LANDAREA_MODE | 182590 | 59.38 | float64 |
| BASEMENTAREA_AVG | 179943 | 58.52 | float64 |
| BASEMENTAREA_MEDI | 179943 | 58.52 | float64 |
| BASEMENTAREA_MODE | 179943 | 58.52 | float64 |
| EXT_SOURCE_1 | 173378 | 56.38 | float64 |
| NONLIVINGAREA_AVG | 169682 | 55.18 | float64 |
| NONLIVINGAREA_MEDI | 169682 | 55.18 | float64 |
| NONLIVINGAREA_MODE | 169682 | 55.18 | float64 |
| ELEVATORS_AVG | 163891 | 53.3 | float64 |
| ELEVATORS_MEDI | 163891 | 53.3 | float64 |
| ELEVATORS_MODE | 163891 | 53.3 | float64 |

## Full Base Table Schema

| column | dtype | missing_count | missing_percent |
| --- | --- | --- | --- |
| SK_ID_CURR | int64 | 0 | 0.0 |
| TARGET | int64 | 0 | 0.0 |
| NAME_CONTRACT_TYPE | str | 0 | 0.0 |
| CODE_GENDER | str | 0 | 0.0 |
| FLAG_OWN_CAR | str | 0 | 0.0 |
| FLAG_OWN_REALTY | str | 0 | 0.0 |
| CNT_CHILDREN | int64 | 0 | 0.0 |
| AMT_INCOME_TOTAL | float64 | 0 | 0.0 |
| AMT_CREDIT | float64 | 0 | 0.0 |
| AMT_ANNUITY | float64 | 12 | 0.0 |
| AMT_GOODS_PRICE | float64 | 278 | 0.09 |
| NAME_TYPE_SUITE | str | 1292 | 0.42 |
| NAME_INCOME_TYPE | str | 0 | 0.0 |
| NAME_EDUCATION_TYPE | str | 0 | 0.0 |
| NAME_FAMILY_STATUS | str | 0 | 0.0 |
| NAME_HOUSING_TYPE | str | 0 | 0.0 |
| REGION_POPULATION_RELATIVE | float64 | 0 | 0.0 |
| DAYS_BIRTH | int64 | 0 | 0.0 |
| DAYS_EMPLOYED | int64 | 0 | 0.0 |
| DAYS_REGISTRATION | float64 | 0 | 0.0 |
| DAYS_ID_PUBLISH | int64 | 0 | 0.0 |
| OWN_CAR_AGE | float64 | 202929 | 65.99 |
| FLAG_MOBIL | int64 | 0 | 0.0 |
| FLAG_EMP_PHONE | int64 | 0 | 0.0 |
| FLAG_WORK_PHONE | int64 | 0 | 0.0 |
| FLAG_CONT_MOBILE | int64 | 0 | 0.0 |
| FLAG_PHONE | int64 | 0 | 0.0 |
| FLAG_EMAIL | int64 | 0 | 0.0 |
| OCCUPATION_TYPE | str | 96391 | 31.35 |
| CNT_FAM_MEMBERS | float64 | 2 | 0.0 |
| REGION_RATING_CLIENT | int64 | 0 | 0.0 |
| REGION_RATING_CLIENT_W_CITY | int64 | 0 | 0.0 |
| WEEKDAY_APPR_PROCESS_START | str | 0 | 0.0 |
| HOUR_APPR_PROCESS_START | int64 | 0 | 0.0 |
| REG_REGION_NOT_LIVE_REGION | int64 | 0 | 0.0 |
| REG_REGION_NOT_WORK_REGION | int64 | 0 | 0.0 |
| LIVE_REGION_NOT_WORK_REGION | int64 | 0 | 0.0 |
| REG_CITY_NOT_LIVE_CITY | int64 | 0 | 0.0 |
| REG_CITY_NOT_WORK_CITY | int64 | 0 | 0.0 |
| LIVE_CITY_NOT_WORK_CITY | int64 | 0 | 0.0 |
| ORGANIZATION_TYPE | str | 0 | 0.0 |
| EXT_SOURCE_1 | float64 | 173378 | 56.38 |
| EXT_SOURCE_2 | float64 | 660 | 0.21 |
| EXT_SOURCE_3 | float64 | 60965 | 19.83 |
| APARTMENTS_AVG | float64 | 156061 | 50.75 |
| BASEMENTAREA_AVG | float64 | 179943 | 58.52 |
| YEARS_BEGINEXPLUATATION_AVG | float64 | 150007 | 48.78 |
| YEARS_BUILD_AVG | float64 | 204488 | 66.5 |
| COMMONAREA_AVG | float64 | 214865 | 69.87 |
| ELEVATORS_AVG | float64 | 163891 | 53.3 |
| ENTRANCES_AVG | float64 | 154828 | 50.35 |
| FLOORSMAX_AVG | float64 | 153020 | 49.76 |
| FLOORSMIN_AVG | float64 | 208642 | 67.85 |
| LANDAREA_AVG | float64 | 182590 | 59.38 |
| LIVINGAPARTMENTS_AVG | float64 | 210199 | 68.35 |
| LIVINGAREA_AVG | float64 | 154350 | 50.19 |
| NONLIVINGAPARTMENTS_AVG | float64 | 213514 | 69.43 |
| NONLIVINGAREA_AVG | float64 | 169682 | 55.18 |
| APARTMENTS_MODE | float64 | 156061 | 50.75 |
| BASEMENTAREA_MODE | float64 | 179943 | 58.52 |
| YEARS_BEGINEXPLUATATION_MODE | float64 | 150007 | 48.78 |
| YEARS_BUILD_MODE | float64 | 204488 | 66.5 |
| COMMONAREA_MODE | float64 | 214865 | 69.87 |
| ELEVATORS_MODE | float64 | 163891 | 53.3 |
| ENTRANCES_MODE | float64 | 154828 | 50.35 |
| FLOORSMAX_MODE | float64 | 153020 | 49.76 |
| FLOORSMIN_MODE | float64 | 208642 | 67.85 |
| LANDAREA_MODE | float64 | 182590 | 59.38 |
| LIVINGAPARTMENTS_MODE | float64 | 210199 | 68.35 |
| LIVINGAREA_MODE | float64 | 154350 | 50.19 |
| NONLIVINGAPARTMENTS_MODE | float64 | 213514 | 69.43 |
| NONLIVINGAREA_MODE | float64 | 169682 | 55.18 |
| APARTMENTS_MEDI | float64 | 156061 | 50.75 |
| BASEMENTAREA_MEDI | float64 | 179943 | 58.52 |
| YEARS_BEGINEXPLUATATION_MEDI | float64 | 150007 | 48.78 |
| YEARS_BUILD_MEDI | float64 | 204488 | 66.5 |
| COMMONAREA_MEDI | float64 | 214865 | 69.87 |
| ELEVATORS_MEDI | float64 | 163891 | 53.3 |
| ENTRANCES_MEDI | float64 | 154828 | 50.35 |
| FLOORSMAX_MEDI | float64 | 153020 | 49.76 |
| FLOORSMIN_MEDI | float64 | 208642 | 67.85 |
| LANDAREA_MEDI | float64 | 182590 | 59.38 |
| LIVINGAPARTMENTS_MEDI | float64 | 210199 | 68.35 |
| LIVINGAREA_MEDI | float64 | 154350 | 50.19 |
| NONLIVINGAPARTMENTS_MEDI | float64 | 213514 | 69.43 |
| NONLIVINGAREA_MEDI | float64 | 169682 | 55.18 |
| FONDKAPREMONT_MODE | str | 210295 | 68.39 |
| HOUSETYPE_MODE | str | 154297 | 50.18 |
| TOTALAREA_MODE | float64 | 148431 | 48.27 |
| WALLSMATERIAL_MODE | str | 156341 | 50.84 |
| EMERGENCYSTATE_MODE | str | 145755 | 47.4 |
| OBS_30_CNT_SOCIAL_CIRCLE | float64 | 1021 | 0.33 |
| DEF_30_CNT_SOCIAL_CIRCLE | float64 | 1021 | 0.33 |
| OBS_60_CNT_SOCIAL_CIRCLE | float64 | 1021 | 0.33 |
| DEF_60_CNT_SOCIAL_CIRCLE | float64 | 1021 | 0.33 |
| DAYS_LAST_PHONE_CHANGE | float64 | 1 | 0.0 |
| FLAG_DOCUMENT_2 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_3 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_4 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_5 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_6 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_7 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_8 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_9 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_10 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_11 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_12 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_13 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_14 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_15 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_16 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_17 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_18 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_19 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_20 | int64 | 0 | 0.0 |
| FLAG_DOCUMENT_21 | int64 | 0 | 0.0 |
| AMT_REQ_CREDIT_BUREAU_HOUR | float64 | 41519 | 13.5 |
| AMT_REQ_CREDIT_BUREAU_DAY | float64 | 41519 | 13.5 |
| AMT_REQ_CREDIT_BUREAU_WEEK | float64 | 41519 | 13.5 |
| AMT_REQ_CREDIT_BUREAU_MON | float64 | 41519 | 13.5 |
| AMT_REQ_CREDIT_BUREAU_QRT | float64 | 41519 | 13.5 |
| AMT_REQ_CREDIT_BUREAU_YEAR | float64 | 41519 | 13.5 |
