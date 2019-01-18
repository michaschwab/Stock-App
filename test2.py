from datetime import *
from pathlib import Path
import pickle
import pandas as pd

columnNames=['Type','Date','Stock Symbol','Quantity','Price','Total Amount']
df2=pd.DataFrame([[1,2,3,4,5,6]],columns=columnNames)
df2.loc[10]=[2,3,4,5,6,7]
print(df2)
