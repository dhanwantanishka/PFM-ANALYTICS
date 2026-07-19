import streamlit as st
import pandas as pd
import pyarrow as pa

df = pd.DataFrame(columns=["date"])
df["date"] = pd.to_datetime(df["date"])
print("Original empty df dtype:", df["date"].dtype)

# Simulate streamlit st.cache_data serialization
table = pa.Table.from_pandas(df)
df_restored = table.to_pandas()

print("Restored empty df dtype:", df_restored["date"].dtype)
