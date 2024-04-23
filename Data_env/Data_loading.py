"""This is a data loading package which imports the data from multiple csv files and create one data frame for
backtesting"""
import glob
import pandas as pd
import warnings
import string
warnings.filterwarnings('ignore')
def data_load(path: string)-> pd.DataFrame:
    global files
    folder = glob.glob(path)
    for file in folder:
        files = glob.glob(file + "/*.csv")
    df = pd.concat([pd.read_csv(files[i]) for i in range(0, len(files))])
    return df