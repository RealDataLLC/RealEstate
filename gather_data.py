from bs4 import BeautifulSoup
import pandas as pd
import requests


class DeptOfNumbersData:
    def __init__(self):
        self.dept_numbers_path = "https://www.deptofnumbers.com/"
        self.dn_jobs_path = "employment/metros/"
        self.get_soup()
        self.get_month()
        
    def get_soup(self):
        print("Accessing the metro employment site")
        page = requests.get(self.dept_numbers_path + self.dn_jobs_path)
        soup = BeautifulSoup(page.text, 'html.parser')
        self.soup = soup
        
    def get_month(self):
        table = self.soup.find('table', {'id': 'metro_table'})
        table_rows = table.find_all('th')
        self.month = table_rows[1].text[:-16]

    def get_jobs_numbers(self, write_csv = False):
        table = self.soup.find('table', {'id': 'metro_table'})
        table_rows = table.find_all('tr')
        l = self.get_table(table_rows)
        
        df = pd.DataFrame(l,columns=["Metro","Month Growth", "Month Growth (%)", "Year Growth", "Year Growth (%)"]).drop(0)
        df = df.sort_values(by="Year Growth (%)", ascending=False)
        
        if (write_csv):
            test = self.month + ".csv"
            df.to_csv("JobsData/" + test)
            print(self.month + ".csv JobsData data logged")
            
        self.jobs_numbers = df
        return df

    
    @staticmethod
    def get_table(table_rows):
        l = []
        for tr in table_rows:
            td = tr.find_all('td')
            row = [tr.text.strip(" %") for tr in td if tr.text.strip()]
            l.append(row)
        return l
    
    def find_city(self, city_name):
        cityName = city_name.lower()
        metroNames = self.jobs_numbers["Metro"].str.lower()
        return self.jobs_numbers[metroNames.str.contains(city_name)]

dept = DeptOfNumbersData()
df = dept.get_jobs_numbers(write_csv=True)