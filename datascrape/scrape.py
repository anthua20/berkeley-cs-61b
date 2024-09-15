import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import numpy as np
def get_random_ip(ip_list):
    # choose ip address from IP lists (the excel file list)
    proxy_list = []
    for ip in ip_list:
        proxy_list.append(ip)
    proxy_ip = np.random.choice(proxy_list)
    proxies = {'http': proxy_ip}
    return proxies

#first page, requesting the search-- pulling the cookies
def request_page(page, ip_list):
    headers = {
        "authority": "pfr.informe.org",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://pfr.informe.org",
        "pragma": "no-cache",
        "referer": "https://pfr.informe.org/ALMSOnline/ALMSQuery/SearchResults.aspx?PageNumber=47",
        "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\", \"Chromium\";v=\"121\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }
    #do a search, right click, hit inspect, go to the Applications tab
    #under storage on the left, go into Cookies, click ASP...
    #cookie value will come up (only works this way this website + this computer)
    cookies = {
        "AspxAutoDetectCookieSupport": "1",
        "ASP.NET_SessionId": "os5jn5s4eg1wvsepheidionf" #first cookie--associated with my session + state
    }
    url = "https://pfr.informe.org/ALMSOnline/ALMSQuery/SearchResults.aspx"
    params = {
        "PageNumber": str(page)
    }
    #send the request to get the search grid (the big table that says Search Results on the Maine site)
    response = requests.post(url, headers=headers, cookies=cookies, params=params, proxies = get_random_ip(ip_list)).text
    bs = BeautifulSoup(response, 'lxml')
    table = bs.find('table', id = 'gvLicensees')
    df_table =pd.read_html(str(table))[0]
    tr_list = bs.find('tbody').find_all('tr')
    href_list = [tr.find('a').attrs['href'] for tr in tr_list]
    df_table['url_detail'] = href_list
    return df_table

#This is asking for the next page--after we click the name a new page comes up, sending the request to get that page
def request_detail(SearchResultToken, ip_list):
    headers = {
        "authority": "pfr.informe.org",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://pfr.informe.org/ALMSOnline/ALMSQuery/SearchResults.aspx?PageNumber=47",
        "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\", \"Chromium\";v=\"121\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }
    cookies = {
        "AspxAutoDetectCookieSupport": "1",
        "ASP.NET_SessionId": "os5jn5s4eg1wvsepheidionf" #second cookie--same value goes here
    }
    url = "https://pfr.informe.org/ALMSOnline/ALMSQuery/ShowDetail.aspx"
    params = {
        "SearchResultToken": SearchResultToken
    }
    # Getting the tables from the person-specific page (history, agency, etc)
    response = requests.get(url, headers=headers, cookies=cookies, params=params, proxies = get_random_ip(ip_list)).text
    bs = BeautifulSoup(response, 'lxml')
    name = bs.find('h2', class_ = 'regulatorName').parent.find_all('h2')[-1].text
    rows = bs.find_all('div', class_ = 'DetailGroup Attributes')[0].find_all('div', class_ = 'attributeRow')
    dict_row = {'Name': name}
    npn = bs.find('div', class_ = 'INDENT1').parent.next_sibling.next_sibling.text
    dict_row['NPN'] = npn
    for row in rows:
        key = row.find_all('div', class_ = 'attributeCell')[0].text.strip()[:-1]
        if key == '':
            continue
        value = row.find_all('div', class_ = 'attributeCell')[1].text.strip()

        dict_row[key] = value
    df_row = pd.DataFrame(dict_row, index = [0])
    try:
        history = bs.find('div', class_ = 'DetailGroup InterpretedLicenseHistory').find('table', class_ = 'tbstriped collapsible')
        df_history = pd.read_html(str(history))[0]
        df_history['License Number Main'] = dict_row['License Number']
    except:
        df_history = pd.DataFrame()

    try:
        suspension = bs.find('div', class_ = 'DetailGroup LicenseSuspensions/LICENSE').find('table', class_ = 'tbstriped collapsible')
        df_suspension = pd.read_html(str(suspension))[0]
        df_suspension['License Number Main'] = dict_row['License Number']
    except:
        df_suspension = pd.DataFrame()

    try:
        agency = bs.find('div', class_ = 'DetailGroup Appointments/AF/Employer').find('table', class_ = 'tbstriped collapsible')
        df_agency = pd.read_html(str(agency))[0]
        df_agency['License Number Main'] = dict_row['License Number']
    except:
        df_agency = pd.DataFrame()

    try:
        employer = bs.find('div', class_ = 'DetailGroup Appointments/AP/Employer').find('table', class_ = 'tbstriped collapsible')
        df_employer = pd.read_html(str(employer))[0]
        df_employer['License Number Main'] = dict_row['License Number']
    except:
        df_employer = pd.DataFrame()

    try:
        authority = bs.find('div', class_ = 'DetailGroup Authorities').find('table', class_ = 'tbstriped collapsible')
        df_authority = pd.read_html(str(authority))[0]
        df_authority['License Number Main'] = dict_row['License Number']
    except:
        df_authority = pd.DataFrame()

    try:
        resolutions = bs.find('div', class_ = 'DetailGroup Resolutions').find('table', class_ = 'tbstriped collapsible')
        df_resolutions = pd.read_html(str(resolutions))[0]
        df_resolutions['License Number Main'] = dict_row['License Number']
    except:
        df_resolutions = pd.DataFrame()

    try:
        relation = bs.find('div', class_ = 'DetailGroup ResponsibleRelations').find('table', class_ = 'tbstriped collapsible')
        df_relation = pd.read_html(str(relation))[0]
        df_relation['License Number Main'] = dict_row['License Number']
    except:
        df_relation = pd.DataFrame()



    try:
        address = bs.find('div', class_ = 'DetailGroup LicenseeBoardAddresses').find('table', class_ = 'tbstriped collapsible')
        df_address = pd.read_html(str(address))[0]
        df_address['License Number Main'] = dict_row['License Number']
    except:
        df_address = pd.DataFrame()

    try:
        unit = bs.find('div', class_ = 'DetailGroup CEUnits').find('table', class_ = 'tbstriped collapsible')
        df_unit = pd.read_html(str(unit))[0]
        df_unit['License Number Main'] = dict_row['License Number']
    except:
        df_unit = pd.DataFrame()

    return df_row, df_history, df_suspension, df_agency, df_employer, df_authority, df_resolutions, df_relation, df_address, df_unit


#Putting the data frames into csvs
if __name__ == '__main__':
    df_ip = pd.read_excel('IP.xlsx')
    ip_list = list(df_ip['IP'])
    df_licenses = pd.DataFrame()
    for page in range(1,5): #this is changed manually, allows longer web scraping when you don't pull the final page # from the website
        print(page)
        df_license = request_page(page, ip_list)
        df_licenses = pd.concat([df_licenses, df_license], ignore_index=True)
    df_licenses.to_csv('列表页.csv', index = False)

    df_rows, df_historys, df_suspensions, df_agencys, df_employers, df_authoritys, df_resolutionss, df_relations, df_addresss, df_units = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


    for row in range(df_licenses.shape[0]):
        if row < 0:
            continue
        print(row)
        SearchResultToken = df_licenses.loc[row, 'url_detail'].split('=')[-1]
        try:
            df_row, df_history, df_suspension, df_agency, df_employer, df_authority, df_resolutions, df_relation, df_address, df_unit = request_detail(SearchResultToken, ip_list)
        except:
            time.sleep(5)
            print('wain')
            df_row, df_history, df_suspension, df_agency, df_employer, df_authority, df_resolutions, df_relation, df_address, df_unit = request_detail(SearchResultToken, ip_list)

        df_rows = pd.concat([df_rows, df_row], ignore_index=True)
        df_historys = pd.concat([df_historys, df_history], ignore_index=True)
        df_suspensions = pd.concat([df_suspensions, df_suspension], ignore_index=True)
        df_employers = pd.concat([df_employers, df_employer], ignore_index=True)

        df_agencys = pd.concat([df_agencys, df_agency], ignore_index=True)
        df_authoritys = pd.concat([df_authoritys, df_authority], ignore_index=True)
        df_resolutionss = pd.concat([df_resolutionss, df_resolutions], ignore_index=True)
        df_relations = pd.concat([df_relations, df_relation], ignore_index=True)
        df_addresss = pd.concat([df_addresss, df_address], ignore_index=True)
        df_units = pd.concat([df_units, df_unit], ignore_index=True)

        time.sleep(2)
    df_rows.to_csv('main.csv', index = False)
    df_historys.to_csv('history.csv', index = False)
    df_suspensions.to_csv('suspension.csv', index = False)
    df_agencys.to_csv('agency.csv', index = False)

    df_employers.to_csv('employer.csv', index = False)
    df_authoritys.to_csv('authority.csv', index = False)
    df_resolutionss.to_csv('resolution.csv', index = False)
    df_relations.to_csv('relation.csv', index = False)
    df_addresss.to_csv('address.csv', index = False)
    df_units.to_csv('unit.csv', index = False)