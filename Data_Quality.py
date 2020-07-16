#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul  5 16:25:45 2020

@author: Fan_L
"""
# Step1: Import excel file##############################################
import pandas as pd
import numpy as np
import seaborn as sns
file = 'KPMG_VI_New_raw_data_update_final.xlsx'
xls = pd.ExcelFile(file)
print(xls.sheet_names)
# Sheet names: 'Title Sheet', 'Transactions', 'NewCustomerList', 
# 'CustomerDemographic', 'CustomerAddress'

# We will only use three datasets for Data Quality Check task: 
# 1. Transactions,
# 2. Customer Demographic
# 3. Customer Address.
# Sheet can be accessed by name or index
Trans = xls.parse('Transactions',skiprows=1)
NewC = xls.parse(2,skiprows=1)
C_info = xls.parse(3,skiprows=1)
C_address = xls.parse(4,skiprows=1)

Trans.name = 'Transactions'
NewC.name = 'New Customer List'
C_info.name = 'Customer Demographic'
C_address.name = 'Customer Address'

# Step2: Set primary keys###############################################
Trans.head()
# After checking the first 5 rows of Transaction dataset, we may consider using
# transaction_id as the primary key.
Trans.transaction_id.nunique() == len(Trans)
# The number of unique values of transaction_id is equal to the number of rows,
# so transaction_id is qualified as a primary key.
Trans = Trans.set_index('transaction_id')
# This step can also be done while importing the dataset: 
# Trans = xls.parse(1, skiprows=1, index_col=0)

# Same steps for the other two dataset
C_info.head()
C_info.customer_id.nunique() == len(C_info)
C_info = C_info.set_index('customer_id')

C_address.head()
C_address.customer_id.nunique() == len(C_address)
C_address = C_address.set_index('customer_id')

# Step3: Check the quality of the datasets###############################
#####################Dataset Trans###################
# 1.1 Overview
Trans.info()
# From the concise summary of the dataset, we know that 
# 1. 20000 records, 12 columns
# 2. 7 columns have missing values 
# ('online_order', 'brand', 'product_line','product_class','product_size',
# 'standard_cost', 'product_first_sold_date' have missing values)
# 3. The data type of product_first_sold_date is not readable
# 4. Online_order could be stored as category.

# 1.2 Null Value
Trans_Null = Trans.isnull().sum().sort_values(ascending = False)
Trans_Null
# pip install missingno
import missingno as msno
msno.matrix(Trans)
# 'brand', 'product_line','product_class','product_size', 'standard_cost', 
# and 'product_first_sold_date' probably have missing values at the same rows
a = set(Trans[Trans.online_order.isnull()].index)
b = set(Trans[Trans.product_line.isnull()].index)
column_contain_nan = ['brand', 'product_line','product_class','product_size', 
                      'standard_cost', 'product_first_sold_date']
for i in column_contain_nan:
    if set(Trans[Trans[i].isnull()].index) == b:
        print('Same rows') 
    else:
        print('Different rows')        
print('The information of brand, product line, product class, '+
      'product size, standard cost, product first sold date is '+
      'missing for transaction: ', 
      Trans[Trans.brand.isnull()].index.values)       
print('The information of online order is missing for transaction: ', 
      Trans[Trans.online_order.isnull()].index.values)        
# a & b     
# For transaction 11016 and 13025, values of all these features are missing.

# 1.3 Consistency
for i in Trans.columns[3:9]:
    print(Trans[i].value_counts())
    
# 1.4 Validity 
for i in [Trans.columns[0:2],Trans.columns[9:13]]:
    print(Trans[i].describe())
# product id: 0-100, customer id:1-5034
Trans.transaction_date.describe()
# Transaction dataset contains transactions happened in 2017.
# 82 Transcations happened on 2017/02/14 (valentine's day)
# Convert timestamp to date
Trans['product_first_sold_date_0'] = pd.to_datetime(Trans.product_first_sold_date,unit='s')
Trans.product_first_sold_date_0.describe()
# The first sold date is 1970/01/01 for all products

# 1.5 Accuracy
sum(Trans.list_price < Trans.standard_cost)
# Price > Cost

# 1.6 Other issue
# Column product_id
# product_id here cannot help us identify a product
# Some items have two list prices and two standard costs, or even four list prices and four standard costs.
# But for item (0,'Norco Bicycles', 'Standard', 'medium', 'medium') & 
#         item (0, 'Solex', 'Road', 'medium', 'medium'), 
# they have a list price but two standard cost    
Product_id_check = Trans.groupby(['product_id', 'brand', 'product_line', 'product_class', 'product_size'])['standard_cost','list_price'].nunique()

# Column customer_id
# Customer whose id is 5034 is not recorded in the customer demographics dataset.

Trans[Trans.customer_id > 4000]


#####################Dataset C_info###################
# 2.1 Overview
C_info.info()
# From the concise summary of the dataset, we know that 
# 1. 4000 records, 12 columns
# 2. 6 columns have missing values 
# ('last_name', 'DOB', 'job_title','job_industry_category','default', 'tenure')

# 2.2 Null Value
C_info_Null = C_info.isnull().sum().sort_values(ascending = False)
C_info_Null
msno.matrix(C_info)
# DOB and tenure robably have missing values at the same rows
sum(C_info.DOB.isnull() != C_info.tenure.isnull())
print('The information of DOB and tenure is missing for Customer: ', 
      C_info[C_info.DOB.isnull()].index.values)     
    
# 2.3 Consistency
for i in C_info.columns[[2,6,7,8,10]]:
    print(C_info[i].value_counts())
# The values in gender column are not consistent
# Wrong spelling of Agriculture
    
# 2.4 Validity
for i in C_info.columns[[3,4,11]]:
    print(C_info[i].describe())
# past 3 year bike related purchases:0-99
# DOB:1843-2002
# tenure: 1-22
sum(C_info.tenure>C_info.age)
C_info.default.describe()
C_info.default
# default column is confusing

# 2.5 Accuracy
# Customers' age
now = pd.Timestamp('now').year
C_info['age'] = now - pd.DatetimeIndex(C_info['DOB']).year
C_info['age_2017'] = 2017 - pd.DatetimeIndex(C_info['DOB']).year
C_info.age.describe()
# 18-177
C_info.age_2017.describe()
sns.boxplot(C_info.age_2017)
# 15-174
# Customer Jephthah  Bachmann, is 177 years old.
C_info[C_info.age == max(C_info.age)]
# This data might be incorrect or outdated

# 2.6 Other issue
# Check whether customer id is truly unique
# by inspecting customers with the same name
C_info_duplicates = C_info.duplicated(subset = ['first_name','last_name'], keep = False)
C_info[C_info_duplicates]
pd.set_option('display.max_columns', None)


#####################Dataset C_address###################
# 3.1 Overview
C_address.info()
# From the concise summary of the dataset, we know that 
# 1. 3999 records, 5 columns
# 2. No missing values 

# 3.2 Null Value

# 3.3 Consistency
# State info is not consistent
for i in C_address.columns[2:4]:
    print(C_address[i].value_counts())

# 3.4 Validity
for i in C_address.columns[[1,4]]:
    print(C_address[i].describe())
# Zip code:2000-4883
# Property valuation: 1-12


#####################Three Datasets Together###################
# Customer_id
Customer_id_trans = set(Trans.customer_id)
Customer_id_info = set(C_info.index)
Customer_id_address = set(C_address.index)
# Customer 3,10,22,23 are not in customer address dataset
Customer_id_info.difference(Customer_id_address)
# Customer 4001, 4002, 4003 are not in customer demographic dataset
Customer_id_address.difference(Customer_id_info)
# Customer 5034 is not in customer demographic dataset
Customer_id_trans.difference(Customer_id_info)

zero_purchase = set(C_info[C_info.past_3_years_bike_related_purchases == 0].index)
zero_purchase & Customer_id_trans
len(zero_purchase & Customer_id_trans)
# 34 customers who purchase 0 bike related products in the past 3 years 
# have purchase records in transaction dataset. The past 3 years might mean the
# time between 2014 and 2016.

d = {'Dataset Name': [],'# of Records': [], '# of Distinct Customer ID': []}
for i in [Trans,C_info,C_address]:
    d['Dataset Name'].append(i.name)
    d['# of Records'].append(i.shape[0])
    try:
        d['# of Distinct Customer ID'].append(i.customer_id.nunique())
    except:
        d['# of Distinct Customer ID'].append(i.index.nunique())
Three_table = pd.DataFrame(d)
