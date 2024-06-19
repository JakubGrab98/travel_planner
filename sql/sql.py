import streamlit as st


connection = st.connection("postgresql", "sql", **st.secrets["postgresql"])

df = connection.query("SELECT * FROM search_parameters;", ttl = "10m")

# st.dataframe(df)

for row in df.itertuples():
    st.write(f"{row.departure_city} has a :{row.destination_city}:")