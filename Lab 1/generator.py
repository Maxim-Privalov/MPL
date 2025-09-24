import pandas as pd
import numpy as np
import os

class Generator:

    work_folder = ""

    def __init__(self, folder):
        self.work_folder = folder

    def generate(self, N):
        for i in range(5):
            df = pd.DataFrame(np.zeros((N, 2)), columns=["category", "value"])
            df["category"] = np.random.choice(["A", "B", 'C', "D"], size=N)
            df["value"] = np.random.uniform(1, 10, size=N)
            df.to_csv(self.work_folder + "/gen" + str(i) + ".csv", index=False)
    

    def is_existed(self):
        flag = True
        for i in range(5):
            flag = os.path.exists(self.work_folder + "/gen" + str(i) + ".csv")
            if not flag:
                return False
        
        return True
    
    def get_data(self, k):
        if (k <= 4 and k >= 0):
            df = pd.read_csv(self.work_folder + "/gen" + str(k) + ".csv")
            return df
        
        return None