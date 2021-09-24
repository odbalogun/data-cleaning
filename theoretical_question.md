## Solving the Theoretical Question

My first step would be to affix appropriate column names to the Master file. This will help avoid ambiguity and make it easier to debug issues. 
The next step will be to search for and remove any rows with duplicate health center names in the same chiefdom. Since there are no instructions on this I will keep the first occurrence of the name and remove all other occurrences.

That done, the next step is to merge both data files. This can be easily done by loading them into Pandas dataframes and running the Pandas merge operation using the health center name as the common column. For example `df_merge = pd.merge(df_1, df_2, on='health_center_name')` .

Alternatively, I might load them into temporary tables in a relational database and then write an SQL LEFT JOIN to merge both tables on the health center name. The result can then be exported to csv or excel as needed.  