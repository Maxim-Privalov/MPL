from concurrent.futures import ProcessPoolExecutor as Pool
import generator as g
import pandas as pd
import numpy as np


def median_standart(df):
    ms_df = pd.DataFrame({"category": [""]*4, "median": [0.0]*4, "std" : [0.0]*4})
    categories = ['A', 'B', 'C', 'D']

    for index, cat in enumerate(categories):
        new_df = df[df['category'] == cat].copy()
        ms_df.loc[index, "category"] = cat
        if not new_df.empty:
            ms_df.loc[index, "median"] = new_df["value"].median()
            ms_df.loc[index, "std"] = new_df["value"].std()
        else:
            ms_df.loc[index, "median"] = np.nan
            ms_df.loc[index, "std"] = np.nan

    return ms_df

def main():
    # Количество значений для категорий
    N = 300000
    # Флаг пересоздания файлов
    RECREATE = False

    g_inst = g.Generator("input")
    if ( (not g_inst.is_existed()) or RECREATE ):
        g_inst.generate(N)

    with Pool(max_workers=5) as executor:
      results = list(executor.map(median_standart, [g_inst.get_data(i) for i in range(5)]))
    print("Медианы и стандартное отклонение по первому файлу")
    print(results[0])

    results_df = pd.concat([res for res in results])
    results_df.rename(columns={"median": "value"}, inplace=True)
    
    last_df = median_standart(results_df)
    print("Медианы и стандартное отклонение по получившемся медианам")
    print(last_df)


if __name__ == '__main__':
    main()