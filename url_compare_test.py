import urllib.parse
import json
import re

def decode_url(url):
    """URL에서 인코딩된 부분을 디코딩하여 사람이 읽기 쉬운 형태로 변환"""
    if '#!' in url:
        # 엔카 URL 구조: [기본 URL]#![인코딩된 JSON]
        base_url, encoded_part = url.split('#!', 1)
        try:
            # 인코딩된 JSON 부분 디코딩
            decoded_json = urllib.parse.unquote(encoded_part)
            
            # JSON 문자열 파싱 시도
            try:
                parsed_json = json.loads(decoded_json)
                # JSON 예쁘게 출력
                pretty_json = json.dumps(parsed_json, ensure_ascii=False, indent=2)
                return f"{base_url}#!\n{pretty_json}"
            except json.JSONDecodeError:
                # JSON 파싱 실패시 그냥 디코딩된 문자열 반환
                return f"{base_url}#!{decoded_json}"
        except:
            # 디코딩 실패시 원본 URL 반환
            return url
    else:
        # '#!' 형식이 아닌 경우 전체 URL 디코딩 시도
        try:
            return urllib.parse.unquote(url)
        except:
            return url

def generate_advanced_search_url(country, manufacturer, model_group, model, 
                                badge_group=None, badge=None, badge_details=None):
    """
    상세 검색 조건에 맞는 엔카 검색 URL 생성
    
    Args:
        country (str): 국산/수입 구분 (Y=국산, N=수입)
        manufacturer (str): 제조사 (예: 기아, 현대)
        model_group (str): 모델 그룹 (예: 스팅어, K5)
        model (str): 모델명 (예: 스팅어, 더 뉴 K5 하이브리드 3세대)
        badge_group (str, optional): 배지 그룹 (예: 가솔린 2000cc)
        badge (str, optional): 배지 (예: 2.0 터보 2WD)
        badge_details (list, optional): 배지 세부사항 목록 (예: ['플래티넘', '드림에디션'])
    
    Returns:
        str: 검색 URL
    """
    base_url = "http://www.encar.com/dc/dc_carsearchlist.do?carType=kor#!"
    
    # 기본 검색 쿼리 구조 설정
    action_query = f"(And.Hidden.N._.(C.CarType.{country}._.(C.Manufacturer.{manufacturer}._.(C.ModelGroup.{model_group}._.C.Model.{model}."
    
    # 배지 그룹이 제공된 경우 추가
    if badge_group:
        action_query += f"_.(C.BadgeGroup.{badge_group}."
        
        # 배지가 제공된 경우 추가
        if badge:
            # 모든 소수점이 있는 숫자(예: 1.6, 2.0, 2.5, 3.3 등)를 X_.Y 형태로 변환
            modified_badge = re.sub(r'(\d+)\.(\d+)', r'\1_.\2', badge)
            action_query += f"_.Badge.{modified_badge}."
        
        # 배지 그룹 닫기
        action_query += ")"
    
    # 나머지 모든 괄호 닫기
    action_query += "))))))"  # 6개의 닫는 괄호
    
    # JSON 형식의 검색 쿼리 생성
    query = {
        "action": action_query,
        "toggle": {},
        "layer": "",
        "sort": "ModifiedDate",
        "page": 1,
        "limit": 20,
        "searchKey": "",
        "loginCheck": False
    }
    
    # JSON을 문자열로 변환 후 URL 인코딩
    json_query = json.dumps(query, ensure_ascii=False)
    encoded_query = urllib.parse.quote(json_query)
    
    return base_url + encoded_query

# 올바른 URL 예시
correct_url = "http://www.encar.com/dc/dc_carsearchlist.do?carType=kor#!%7B%22action%22%3A%22(And.Hidden.N._.(C.CarType.Y._.(C.Manufacturer.%EA%B8%B0%EC%95%84._.(C.ModelGroup.%EC%8A%A4%ED%8C%85%EC%96%B4._.(C.Model.%EC%8A%A4%ED%8C%85%EC%96%B4._.(C.BadgeGroup.%EA%B0%80%EC%86%94%EB%A6%B0%202000cc._.Badge.2_.0%20%ED%84%B0%EB%B3%B4%202WD.))))))%22%2C%22toggle%22%3A%7B%7D%2C%22layer%22%3A%22%22%2C%22sort%22%3A%22ModifiedDate%22%2C%22page%22%3A1%2C%22limit%22%3A20%2C%22searchKey%22%3A%22%22%2C%22loginCheck%22%3Afalse%7D"

# 문제가 있는 URL 예시 (OR 조건 포함)
problematic_url = "http://www.encar.com/dc/dc_carsearchlist.do?carType=kor#!%7B%22action%22%3A%20%22%28And.Hidden.N._.%28C.CarType.Y._.%28C.Manufacturer.%EA%B8%B0%EC%95%84._.%28C.ModelGroup.%EC%8A%A4%ED%8C%85%EC%96%B4._.Model.%EC%8A%A4%ED%8C%85%EC%96%B4._.%28C.BadgeGroup.%EA%B0%80%EC%86%94%EB%A6%B0%202000cc._.%28C.Badge.2.0%20%ED%84%B0%EB%B3%B4%202WD._.%28Or.BadgeDetail.%ED%94%8C%EB%9E%98%ED%8B%B0%EB%84%98._.BadgeDetail.%EB%93%9C%EB%A6%BC%EC%97%90%EB%94%94%EC%85%98.%29%29%29%29%29%29%29%22%2C%20%22toggle%22%3A%20%7B%7D%2C%20%22layer%22%3A%20%22%22%2C%20%22sort%22%3A%20%22ModifiedDate%22%2C%20%22page%22%3A%201%2C%20%22limit%22%3A%2020%2C%20%22searchKey%22%3A%20%22%22%2C%20%22loginCheck%22%3A%20false%7D"

print("\n" + "=" * 60)
print("엔카 URL 비교 테스트")
print("=" * 60)

# 올바른 URL 디코딩 및 분석
print("\n[1. 올바른 URL 형식]")
print("디코딩된 URL:")
print(decode_url(correct_url))

# 잘못된 URL 디코딩 및 분석
print("\n[2. 문제가 있는 URL 형식]")
print("디코딩된 URL:")
print(decode_url(problematic_url))

# 직접 URL 생성 및 비교
print("\n[3. 코드로 생성한 URL]")
country = "Y"
manufacturer = "기아"
model_group = "스팅어"
model = "스팅어"
badge_group = "가솔린 2000cc"
badge = "2.0 터보 2WD"

generated_url = generate_advanced_search_url(
    country, manufacturer, model_group, model, badge_group, badge
)

print("생성된 URL:")
print(generated_url)
print("\n디코딩된 URL:")
print(decode_url(generated_url))

# URL 구조 비교 분석
print("\n[4. URL 형식 비교 분석]")

# 올바른 URL과 생성된 URL 비교
print("\n올바른 URL과 생성된 URL의 일치 여부:")
is_match = generated_url == correct_url
print(f"일치함: {is_match}")

# 일치하지 않는 경우 차이점 분석
if not is_match:
    print("\n차이점 분석:")
    
    # 디코딩된 JSON 비교
    correct_json_str = urllib.parse.unquote(correct_url.split('#!', 1)[1])
    generated_json_str = urllib.parse.unquote(generated_url.split('#!', 1)[1])
    
    try:
        correct_json = json.loads(correct_json_str)
        generated_json = json.loads(generated_json_str)
        
        # action 비교
        if correct_json.get("action") != generated_json.get("action"):
            print("\n[액션 부분 차이]")
            print(f"올바른 URL 액션: {correct_json.get('action')}")
            print(f"생성된 URL 액션: {generated_json.get('action')}")
            
            # 공백 및 특수 문자 확인
            print("\n[공백 및 특수 문자 확인]")
            correct_action = correct_json.get("action", "")
            generated_action = generated_json.get("action", "")
            
            for i, (c1, c2) in enumerate(zip(correct_action, generated_action)):
                if c1 != c2:
                    print(f"위치 {i}: '{c1}' vs '{c2}' (ASCII: {ord(c1)} vs {ord(c2)})")
        
        # 다른 속성 비교
        print("\n[기타 속성 비교]")
        all_keys = set(correct_json.keys()) | set(generated_json.keys())
        for key in all_keys:
            if key != "action" and correct_json.get(key) != generated_json.get(key):
                print(f"{key}: {correct_json.get(key)} vs {generated_json.get(key)}")
    
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")

print("\n" + "=" * 60)
print("테스트 종료")
print("=" * 60) 