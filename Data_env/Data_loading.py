"""This is a data loading package which imports the data from multiple csv files and create one data frame for
backtesting"""
import glob
import pandas as pd
import warnings
import string
warnings.filterwarnings('ignore')
def data_load(path: string)-> pd.DataFrame:
