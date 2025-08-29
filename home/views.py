from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
import requests
import json
import numpy as np
from itertools import chain

# 카카오맵 REST API 키를 여기에 입력하세요.
KAKAO_API_KEY = "49c4e816c2cc2cf107b096a896a7c41a"

# 주소를 위도, 경도로 변환하는 함수
def geocode_address(address):
    url = f"https://dapi.kakao.com/v2/local/search/address.json?query={address}"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    try:
        response = requests.get(url, headers=headers).json()
        if response['documents']:
            x = float(response['documents'][0]['x'])
            y = float(response['documents'][0]['y'])
            return y, x
    except Exception as e:
        print(f"Error geocoding {address}: {e}")
    return None, None


def get_cafe_data():
    Servicekey = "15436553a932cf5f1b6c3bfde7344b1926a1972e5b5790ad49dba674c3649a65"
    base_url = "https://api.odcloud.kr/api"
    url = "/15038007/v1/uddi:bd3991e5-97b3-4ffd-bb50-8ef497883efe"
    all_data = []
    per_page_limit = 10 # API 제한에 맞춰 10개로 설정
    
    for page_num in range(1, 11): 
        params = {
            'serviceKey': Servicekey,
            'page': page_num,
            'perPage': per_page_limit,
            'returnType': "json"
        }

        try:
            response = requests.get(base_url + url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and data['data']:
                all_data.append(data['data'])
            else:
                # 더 이상 데이터가 없으면 루프 종료
                break

        except requests.exceptions.RequestException as e:
            print(f"API 요청 오류: {e}")
            return []
        except ValueError as e:
            print(f"API 응답 형식 오류: {e}")
            return []
    
    # 여러 페이지의 데이터를 하나의 리스트로 합치기
    flat_data = list(chain.from_iterable(all_data))
    
    if not flat_data:
        print("모든 API 요청에서 데이터를 가져오는 데 실패했습니다.")
        return []

    try:
        df = pd.DataFrame(flat_data)
        
        df = df.drop(columns=['소재지(지번)', '소재지전화','업종명', '업태명', '연번', '영업장면적'], errors='ignore')
        df = df.dropna(subset=['소재지(도로명)'])
        df = df.drop_duplicates(subset=['업소명', '소재지(도로명)'])
        
        df['위도'], df['경도'] = zip(*df['소재지(도로명)'].apply(geocode_address))
        
        # NaN 값을 None으로 변환
        df = df.replace({np.nan: None}) 
        
        cafes = df.to_dict('records')
        
        return cafes
    except KeyError as e:
        print(f"데이터프레임 처리 중 키 오류: {e}")
        return []

def map_view(request):
    """지도를 표시하는 HTML 페이지를 렌더링합니다."""
    return render(request, 'cafe/map.html')

def cafe_data_api(request):
    """카페 데이터를 JSON으로 제공하는 API 뷰입니다."""
    cafes = get_cafe_data()
    # 유효한 위경도 데이터만 필터링
    valid_cafes = [cafe for cafe in cafes if cafe['위도'] is not None and cafe['경도'] is not None]
    return JsonResponse(valid_cafes, safe=False)