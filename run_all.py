import pandas as pd
import pandas as pd
import matplotlib.pyplot as plt

# importing data
# data = pd.read_csv("data/data.csv")
# data_2014_2024 = data[(pd.to_datetime(data["date"]).dt.year >= 2014) & (pd.to_datetime(data["date"]).dt.year <= 2024)]
# data_2014_2024.to_csv("data/data_2014_2024.csv", index=False)

data_2014_2024 = pd.read_csv("data/data_2014_2024.csv")
indicator_df = pd.read_csv("data/indicators.csv")
region_df = pd.read_csv("data/regions.csv")
better_crime_df = pd.read_csv("data/better_crime.csv")

# cleaning the crime dataset
# sorting by city length to get rid of entries where the city is not specified
better_crime_df = better_crime_df[better_crime_df["address_city"].str.len() > 2]
crime_2014_2024 = better_crime_df[(better_crime_df["year"] >= 2014) & (better_crime_df["year"] <= 2024)]

# creating city_state and year_city_state columns for merging later
crime_2014_2024["city_state"] = crime_2014_2024["address_city"].str.capitalize() + ", " + crime_2014_2024["address_state"].str.upper()
crime_2014_2024["year_city_state"] = crime_2014_2024["year"].astype(str) + ": " + crime_2014_2024["city_state"]

# adding city state combos with the same year together 
crime_2014_2024_1 = crime_2014_2024[["year", "city_state", "year_city_state", "actual_murder", "actual_rape_total", "actual_robbery_total", "actual_assault_total", "actual_theft_total"]].copy()
crime_clean = crime_2014_2024_1.groupby(["year", "city_state", "year_city_state"]).agg("sum").reset_index()

# filter zillow data, looking at specific indicator ids(only home values)
data_2014_2024["date"] = pd.to_datetime(data_2014_2024["date"])
data_2014_2024["year"] = data_2014_2024["date"].dt.year
indicator_filter = ['ZATT', 'ZSFH', 'ZALL', 'ZCON', 'ZABT', 'Z5BR', 'Z2BR', 'Z3BR', 'Z1BR', 'Z4BR']
data_2014_2024 = data_2014_2024[data_2014_2024.indicator_id.isin(indicator_filter)]

# keep latest house listing for each year
data_2014_2024_clean = data_2014_2024.sort_values(by=["date", "indicator_id", "region_id"], ascending=[False, True, True]).drop_duplicates(subset=["year", "indicator_id", "region_id"], keep="first").reset_index()

# merge housing value data with region data
merged_df = pd.merge(data_2014_2024_clean, region_df, on="region_id", how="left")

# filter region data to only include regions present in the cleaned housing data
check_merge = region_df[region_df["region_id"].isin(data_2014_2024_clean["region_id"])]

# separate merged data by region type
check_merge_zip = check_merge[check_merge["region_type"] == "zip"].copy()
check_merge_metro = check_merge[check_merge["region_type"] == "metro"].copy()
check_merge_neigh = check_merge[check_merge["region_type"] == "neigh"].copy()
check_merge_city = check_merge[check_merge["region_type"] == "city"].copy()
check_merge_county = check_merge[check_merge["region_type"] == "county"].copy()

# parsing data from region type zip
check_merge_zip.loc[:, "city"] = check_merge_zip["region"].str.split(";").str[3]
check_merge_zip.loc[:, "state"] = check_merge_zip["region"].str.split(";").str[1]

# rename metro region column as region as city and state already 
check_merge_metro = check_merge_metro.rename(columns={"region": 'city_state'})

# parsing data from region type neigh
check_merge_neigh.loc[:, "city"] = check_merge_neigh["region"].str.split(";").str[4]
check_merge_neigh.loc[:, "state"] = check_merge_neigh["region"].str.split(";").str[1]

# parsing data from region type city
check_merge_city.loc[:, "city"] = check_merge_city["region"].str.split(";").str[0]
check_merge_city.loc[:, "state"] = check_merge_city["region"].str.split(";").str[1]

# parsing data from region type county
check_merge_county.loc[:, "city"] = check_merge_county["region"].str.split(";").str[0]
check_merge_county.loc[:, "state"] = check_merge_county["region"].str.split(";").str[1]

# merge all region types back together
check_merge_combine = pd.concat([check_merge_zip, check_merge_metro, check_merge_neigh, check_merge_city, check_merge_county], ignore_index=True)

# merge cleaned housing data with cleaned region data
merged_df_clean = pd.merge(data_2014_2024_clean, check_merge_combine.drop(["region_type","region"], axis=1), on="region_id", how="inner")
merged_df_clean["date"] = pd.to_datetime(merged_df_clean["date"])

# create city_state column for merging later
merged_df_clean["city_state"] = merged_df_clean["city"] + ", " + merged_df_clean["state"]

# merge all zillow data together
final_zilow_df = pd.merge(merged_df_clean, indicator_df, on="indicator_id", how="inner")

# create year_city_state column in final zillow dataset for merging later
final_zilow_df["year_city_state"] = final_zilow_df["date"].dt.year.astype(str) + ": " + final_zilow_df["city_state"]

# merge final zillow data with cleaned crime data
final_df = pd.merge(final_zilow_df, crime_clean, on="year_city_state", how="inner")

# create a new columne to see the total crime in each city per year
final_df["total_crime"] = final_df["actual_murder"] + final_df["actual_rape_total"] + final_df["actual_robbery_total"] + final_df["actual_assault_total"] + final_df["actual_theft_total"]

# Select and rename columns
final_df = final_df[["date", "year_x", "city_state_x", "year_city_state", "indicator_id", "indicator", "value", "actual_murder", "actual_rape_total", "actual_robbery_total", "actual_assault_total", "actual_theft_total"]]
final_df.columns = ["date", "year", "city_state", "year_city_state", "indicator_id", "indicator", "value", "actual_murder", "actual_rape_total", "actual_robbery_total", "actual_assault_total", "actual_theft_total"]

# output final dataframe to csv
final_df.to_csv("output/final_df.csv", index=False)

# collect Top 5 city_states with highest average crime over 2014-2024
top_5_crime_values = final_df.groupby("city_state")[["total_crime", "value"]].mean().nlargest(5, "total_crime")
top_5_crime_values_df = final_df[final_df["city_state"].isin(top_5_crime_values.index)]
top_5_crime_values_df = top_5_crime_values_df.groupby(["year", "city_state"])[["total_crime", "value"]].mean().reset_index()

# Line graph showing total crime for each year of top 5 cities with highest average crime from 2014-2024 
plt.figure(figsize=(14, 8))
for city in top_5_crime_values_df['city_state'].unique():
    city_data = top_5_crime_values_df[top_5_crime_values_df['city_state'] == city]
    plt.plot(city_data['year'], city_data['total_crime'], marker='o', label=city)

plt.xlabel('Year')
plt.ylabel('Total Crime')
plt.title('Top 5 Cities with Total Crime - Crime Trends (2014-2025)')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('output/top_5_crime_trends.png')

# Line graph showing the home value of Top 5 Cities with Crime by year
plt.figure(figsize=(14, 8))
for city in top_5_crime_values_df['city_state'].unique():
    city_data = top_5_crime_values_df[top_5_crime_df['city_state'] == city]
    plt.plot(city_data['year'], city_data['value'], marker='o', label=city)

plt.xlabel('Year')
plt.ylabel('Total Crime')
plt.title('Top 5 Cities with Total Crime - Mean Home Value Trends (2014-2025)')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('output/top_5_home_value_trends.png')

# Dual-axis line graph for a specific city (e.g., Chicago, IL)

def bar_graph_crime_values(city_state):

    # 1. Define the city variable
    city_data = top_5_crime_values_df[top_5_crime_values_df.city_state == city_state]

    # 2. Setup the figure and the first axis (for House Value)
    fig, ax1 = plt.subplots(figsize=(14, 8))

    # Plot House Value on the left axis (ax1)
    line1 = ax1.plot(city_data['year'], city_data['value'], marker='o', color='blue', label=f'{city_state} House Value')

    ax1.set_xlabel('Year')
    ax1.set_ylabel('House Value', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # 3. Setup the second axis (for Crime)
    ax2 = ax1.twinx()  

    # Plot Crime on the right axis (ax2)
    line2 = ax2.plot(city_data['year'], city_data['total_crime'], marker='o', color='red', label=f'{city_state} Crime')

    ax2.set_ylabel('Total Crime', color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    # 4. Final touches
    plt.title(f'{city_state} House Value and Crime (2014-2024)')
    plt.grid(True, alpha=0.3)

    # Combine legends from both axes
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')

    plt.tight_layout()
    plt.savefig(f'output/{city_state.replace(", ", "_").replace(" ", "_").lower()}_house_value_crime_trends.png')

for city_state in top_5_crime_values_df.city_state.unique():
    bar_graph_crime_values(city_state)