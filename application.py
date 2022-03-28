from datetime import datetime, date

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import json

#accetoken, refreshtoken 등을 가져오는 함수
#결과값은 아래와 같음(예시)
# {'access_token': 'ipl3qZvJHGnKRcJcWwOwRGCiknant6SMWNQZjQopb1UAAAF_SsFBzg',
# 'token_type': 'bearer',
# 'refresh_token': '83nRuhkEH562FuXsdyv3Uy645iwSoJ8THoMyyQopb1UAAAF_SsFBzQ',
# 'expires_in': 21599,
# 'scope': 'talk_message',
# 'refresh_token_expires_in': 5183999}

def getTokens():
# kauth.kakao.com/oauth/authorize?client_id=dfe898e67ff83b6b27021d9fc1e06503&redirect_uri=https://example.com/oauth&response_type=code
    url = 'https://kauth.kakao.com/oauth/token'
    data = {
        'grant_type': 'authorization_code',
        'client_id': 'dfe898e67ff83b6b27021d9fc1e06503',
        'redirect_uri': 'https://example.com/oauth',
        'code': 'jGX1gpwxVzKgQlcGN08r-z75GPt_8FMBYu1mQ-_-kfP2ncAil5vBT2sAdefiV5aWqlAy-gorDR4AAAF_T-wktA'
    }

    response = requests.post(url, data=data)
    tokens = response.json()

    return tokens

def renewAccessToken(refresh_token) -> str:
    REST_API_KEY = "자신의 REST API KEY"
    REDIRECT_URI = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",  # 얘는 단순 String임. "refresh_token"
        "client_id": "dfe898e67ff83b6b27021d9fc1e06503",
        "refresh_token": refresh_token  # 여기가 위에서 얻은 refresh_token 값
    }

    resp = requests.post(REDIRECT_URI, data=data)
    new_token = resp.json()

    return new_token['access_token']



#==================================================================================================================
def get_IPO_public_schedule_data_from_38(page=1):
    total_data = []
    for p in range(1, page + 1):
        fullUrl = 'http://www.38.co.kr/html/fund/index.htm?o=k&page=%s' % p
        response = requests.get(fullUrl, headers={'User-Agent' : 'Mozilla/5.0'})
        html = response.text
        soup = BeautifulSoup(html, 'lxml')
        data = soup.find('table', {'summary': '공모주 청약일정'})
        data = data.find_all('tr')[2:]
        total_data = total_data + data

    company_list = []
    public_date_list = []
    price_list = []
    band_list = []
    competition_rate_list = []
    underwriter_list = []

    for row in range(0, len(total_data)):
        data_list = total_data[row].text.replace('\xa0', '').replace('\t\t', '').split('\n')[1:-1]
        if len(data_list) < 6:
            continue

        todayWeekNo = datetime.today().date().isocalendar().week
        date_string = data_list[1].strip()[0:10].replace('.', '-')
        publicWeekNo =  date(*map(int, date_string.split('-'))).isocalendar().week

        if todayWeekNo == publicWeekNo:
            company_list.append(data_list[0].replace('(유가)', '').strip())
            public_date_list.append(data_list[1].strip())
            price_list.append(data_list[2].strip())
            band_list.append(data_list[3].strip())
            competition_rate_list.append(data_list[4].strip())
            underwriter_list.append(data_list[5].strip())
    # print(company_list)
    # print(public_date_list)
    # print(price_list)
    # print(band_list)
    # print(competition_rate_list)
    # print(underwriter_list)

    jsonData = []

    str = ''
    for i in range(0, len(company_list)):
        str += company_list[i] + " / " + public_date_list[i] + " / " + price_list[i] + "원 / " + underwriter_list[i] + '\n\n'
        # jsonData.append({
        #     "회사": company_list[i],
        #     #"청약일": public_date_list[i],
        #     "공모가": price_list[i],
        #     #"밴드가격": band_list[i],
        #     #"경쟁률": competition_rate_list[i],
        #     "주관": underwriter_list[i]
        # })

    dump = json.dumps(jsonData, ensure_ascii = False)
    print(str)
    return str


#여기가 메인 => 여기서 실행하면 됨
if __name__ == '__main__':

    public_schedule = get_IPO_public_schedule_data_from_38()

    # getTokens를 한달에 한번 실행해서 refreshToken을 받아옴
    # 받아온 refreshToken은 한달동안 사용하여 renewAccessToken 호출 및 renewedToken 받아옴
    # 받아온 renewedToken은 access token으로, 메시지 전송 시 사용


    if(datetime.today().day == 1):
        code = getTokens()
        refreshToken = code['refresh_token']
        currentRefreshToken = refreshToken
    else:
        refreshToken = 'x4b0YURBdomuOEL5PdlVg2d-xjn3WtP-toz3Ago9dJcAAAF_T-x_tQ'

    renewedToken = renewAccessToken(refreshToken)

    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": 'Bearer ' + renewedToken}
    data = {
        "template_object": json.dumps({
            "object_type": "text",
            "text" : public_schedule,
            "link":{
                "web_url":"www.naver.com"
            }
        })
    }

    response = requests.post(url, headers=headers, data=data)
    print(response.status_code)
    if response.json().get('result_code') == 0:
        print('메시지를 성공적으로 보냈습니다.')
    else:
        print('메시지를 성공적으로 보내지 못했습니다. 오류메시지 : ' + str(response.json()))
