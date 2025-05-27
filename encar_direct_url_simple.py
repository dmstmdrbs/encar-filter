import time
import json
import os
import urllib.parse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

def extract_car_id_from_url(detail_url):
    try:
        if "dc_cardetailview.do" in detail_url:
            query_params = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(detail_url).query))
            return query_params.get('carid')
        elif "/cars/detail/" in detail_url:
            return detail_url.split('/')[-1].split('?')[0]
    except Exception as e:
        print(f"carId 추출 실패: {e}")
    return None

def extract_number(text):
    num_text = ''.join(filter(str.isdigit, text))
    return int(num_text) if num_text else None

def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def set_limit_in_search_url(url, new_limit=1000):
    """엔카 검색 URL의 limit 파라미터를 항상 new_limit 값으로 세팅"""
    if '#!' not in url:
        return url
    base_url, encoded_json = url.split('#!', 1)
    decoded_json = urllib.parse.unquote(encoded_json)
    try:
        query = json.loads(decoded_json)
        query['limit'] = str(new_limit)
        new_encoded_json = urllib.parse.quote(json.dumps(query, ensure_ascii=False))
        return f"{base_url}#!{new_encoded_json}"
    except Exception as e:
        print(f"limit 자동설정 실패: {e}")
        return url

class EncarCrawler:
    def __init__(self, headless=True):
        self.headless = headless
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        if self.headless:
            options.add_argument('--headless')
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    def fetch_listings(self, search_url):
        driver = self.setup_driver()
        try:
            driver.get(search_url)
            time.sleep(5)
            car_items = driver.find_elements(By.CSS_SELECTOR, "table.car_list tr[data-index]")
            listings = []
            for item in car_items:
                car_id = item.get_attribute('data-impression').split('|')[0]
                # 가격 추출
                try:
                    price_element = item.find_element(By.CSS_SELECTOR, "td.prc_hs strong")
                    price = price_element.text.strip() + "만원"
                except Exception:
                    price = ""
                # 지역 추출
                try:
                    region_element = item.find_element(By.CSS_SELECTOR, "td.inf span.detail span.loc")
                    region = region_element.text.strip()
                except Exception:
                    region = ""
                # 제목 추출: <a> 태그의 텍스트 전체를 합침
                try:
                    a_tag = item.find_element(By.CSS_SELECTOR, "td.inf a")
                    title = a_tag.text.strip()
                except Exception:
                    title = ""
               
                detail_link = f"https://fem.encar.com/cars/detail/{car_id}"
                detail_info = "..."  # (상세정보 추출 코드)
                listings.append({
                    'id': car_id,
                    'title': title,
                    'price': price,
                    'region': region,
                    'link': detail_link,
                    'detail': detail_info
                })
            return listings
        finally:
            driver.quit()
    def fetch_detail(self, detail_url):
        driver = self.setup_driver()
        try:
            driver.get(detail_url)
            time.sleep(3)
            # 성능기록부, 특이사항 등 파싱
            performance_data = self.parse_performance_data(driver)
            special_note = self.parse_special_note(driver)
            return performance_data, special_note
        finally:
            driver.quit()
    def parse_performance_data(self, driver):
        try:
            wait = WebDriverWait(driver, 10)
            performance_section = driver.find_elements(By.XPATH, "//div[@data-impression='성능기록부']")
            performance_data = {'교환': 999, '판금': 999, '부식': 999}
            if not performance_section:
                print("성능기록부 영역을 찾을 수 없습니다.")
                return None
            check_list = performance_section[0].find_elements(By.XPATH, ".//ul[contains(@class, 'DetailInspect_check_list')]")
            if not check_list:
                list_items = performance_section[0].find_elements(By.TAG_NAME, "li")
                if not list_items:
                    print("성능기록부 항목을 찾을 수 없습니다.")
                    return None
                for item in list_items:
                    item_text = item.text.strip()
                    if '교환' in item_text:
                        if '없음' in item_text:
                            performance_data['교환'] = 0
                        else:
                            num_text = ''.join(filter(str.isdigit, item_text))
                            if num_text:
                                performance_data['교환'] = int(num_text)
                    elif '판금' in item_text:
                        if '없음' in item_text:
                            performance_data['판금'] = 0
                        else:
                            num_text = ''.join(filter(str.isdigit, item_text))
                            if num_text:
                                performance_data['판금'] = int(num_text)
                    elif '부식' in item_text:
                        if '없음' in item_text:
                            performance_data['부식'] = 0
                        else:
                            num_text = ''.join(filter(str.isdigit, item_text))
                            if num_text:
                                performance_data['부식'] = int(num_text)
            else:
                list_items = check_list[0].find_elements(By.TAG_NAME, "li")
                if not list_items:
                    print("체크리스트 항목을 찾을 수 없습니다.")
                    return None
                for item in list_items:
                    item_text = item.text.strip()
                    p_tags = item.find_elements(By.TAG_NAME, "p")
                    if len(p_tags) >= 2:
                        category = p_tags[0].text.strip()
                        value_text = p_tags[1].text.strip()
                        if '교환' in category:
                            if '없음' in value_text:
                                performance_data['교환'] = 0
                            else:
                                span_elements = p_tags[1].find_elements(By.TAG_NAME, "span")
                                if span_elements:
                                    num_text = span_elements[0].text.strip()
                                else:
                                    num_text = ''.join(filter(str.isdigit, value_text))
                                if num_text:
                                    performance_data['교환'] = int(num_text)
                        elif '판금' in category:
                            if '없음' in value_text:
                                performance_data['판금'] = 0
                            else:
                                span_elements = p_tags[1].find_elements(By.TAG_NAME, "span")
                                if span_elements:
                                    num_text = span_elements[0].text.strip()
                                else:
                                    num_text = ''.join(filter(str.isdigit, value_text))
                                if num_text:
                                    performance_data['판금'] = int(num_text)
                        elif '부식' in category:
                            if '없음' in value_text:
                                performance_data['부식'] = 0
                            else:
                                span_elements = p_tags[1].find_elements(By.TAG_NAME, "span")
                                if span_elements:
                                    num_text = span_elements[0].text.strip()
                                else:
                                    num_text = ''.join(filter(str.isdigit, value_text))
                                if num_text:
                                    performance_data['부식'] = int(num_text)
            print(f"추출된 성능기록부 데이터: {performance_data}")
            if performance_data['교환'] == 999 and performance_data['판금'] == 999 and performance_data['부식'] == 999:
                return None
            return performance_data
        except Exception as e:
            print(f"성능기록부 파싱 중 오류: {e}")
            return None
    def parse_special_note(self, driver):
        try:
            car_history_section = driver.find_elements(By.XPATH, "//div[@data-impression='차량이력']")
            special_note = None
            if car_history_section:
                special_note_li = car_history_section[0].find_elements(
                    By.XPATH, ".//li[p[contains(text(), '특이 사항')]]"
                )
                if special_note_li:
                    ul = special_note_li[0].find_elements(By.TAG_NAME, "ul")
                    if ul and ul[0].text.strip():
                        special_note = ul[0].text.strip()
                    else:
                        special_note = "없음"
            print(f"특이사항: {special_note}")
            return special_note
        except Exception as e:
            print(f"특이사항 파싱 중 오류: {e}")
            return None

class CarConditionFilter:
    def is_good_car(self, performance_data, special_note):
        # None 체크
        if not performance_data or special_note is None:
            return False
        exchange = performance_data.get('교환', 999)
        panel = performance_data.get('판금', 999)
        corrosion = performance_data.get('부식', 999)
        # 조건: 교환 1건 이하, 판금 0건, 부식 0건, 특이사항(용도이력) 없음
        return (
            exchange <= 1 and
            panel == 0 and
            corrosion == 0 and
            (special_note == "없음")
        )

class CarListingRepository:
    def __init__(self, data_file, good_cars_file):
        self.data_file = data_file
        self.good_cars_file = good_cars_file
    def load_known_listings(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get("listings", []))
        return set()
    def save_known_listings(self, known_listings):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump({"listings": list(known_listings)}, f)
    def load_good_cars(self):
        if os.path.exists(self.good_cars_file):
            with open(self.good_cars_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("cars", [])
        return []
    def save_good_cars(self, good_cars):
        with open(self.good_cars_file, 'w', encoding='utf-8') as f:
            json.dump({"cars": good_cars}, f, ensure_ascii=False, indent=2)


class EncarMonitor:
    def __init__(self, search_url, check_interval, repo, crawler, filter):
        self.search_url = search_url
        self.check_interval = check_interval
        self.repo = repo
        self.crawler = crawler
        self.filter = filter
        self.known_listings = self.repo.load_known_listings()
        self.good_cars = self.repo.load_good_cars()
    def run(self):
        print(f"매물 모니터링을 시작합니다.")
        print(f"검색 URL (인코딩됨): {self.search_url}")
        print(f"검색 간격: {self.check_interval}초")
        try:
            while True:
                print("\n" + "="*50)
                print(f"매물 확인 시작: {now_str()}")
                new_listings = []
                listings = self.crawler.fetch_listings(self.search_url)
                for listing in listings:
                    item_id = listing['id']
                    if item_id in self.known_listings:
                        continue
                    performance_data, special_note = self.crawler.fetch_detail(listing['link'])
                    is_good_car = self.filter.is_good_car(performance_data, special_note)
                    listing['is_good_car'] = is_good_car
                    if is_good_car:
                        self.good_cars.append({
                            'carId': item_id,
                            'url': listing['link'],
                            'title': listing['title'],
                            'exchange': performance_data.get('교환', 999),
                            'panel': performance_data.get('판금', 999),
                            'corrosion': performance_data.get('부식', 999),
                            'special_note': special_note,
                            'price': listing.get('price', ''),
                            'region': listing.get('region', ''),
                            'check_time': now_str()
                        })
                        self.repo.save_good_cars(self.good_cars)
                    new_listings.append(listing)
                    self.known_listings.add(item_id)
                if new_listings:
                    print(f"새로운 매물 {len(new_listings)}개가 발견되었습니다!")
                    # if self.notifier and self.email_to:
                    #     self.notifier.send(self.email_to, new_listings)
                else:
                    print("새로운 매물이 없습니다.")
                self.repo.save_known_listings(self.known_listings)
                print(f"다음 검색 시간: {datetime.now().fromtimestamp(time.time() + self.check_interval).strftime('%Y-%m-%d %H:%M:%S')}")
                print("="*50)
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            print("\n모니터링을 종료합니다.")
            self.repo.save_known_listings(self.known_listings)
            self.repo.save_good_cars(self.good_cars)

# main 함수 예시
if __name__ == "__main__":
    search_url = "http://www.encar.com/dc/dc_carsearchlist.do?carType=kor#!%7B%22action%22%3A%22(And.Hidden.N._.Options.%ED%81%AC%EB%A3%A8%EC%A6%88%20%EC%BB%A8%ED%8A%B8%EB%A1%A4(%EC%96%B4%EB%8C%91%ED%8B%B0%EB%B8%8C_)._.Options.360%EB%8F%84%20%EC%96%B4%EB%9D%BC%EC%9A%B4%EB%93%9C%20%EB%B7%B0._.(C.CarType.Y._.(C.Manufacturer.%EA%B8%B0%EC%95%84._.(C.ModelGroup.%EC%8A%A4%ED%8C%85%EC%96%B4._.(C.Model.%EC%8A%A4%ED%8C%85%EC%96%B4._.BadgeGroup.%EA%B0%80%EC%86%94%EB%A6%B0%202000cc.)))))%22%2C%22toggle%22%3A%7B%7D%2C%22layer%22%3A%22%22%2C%22sort%22%3A%22ModifiedDate%22%2C%22page%22%3A1%2C%22limit%22%3A%22300%22%2C%22searchKey%22%3A%22%22%2C%22loginCheck%22%3Afalse%7D"
    search_url = set_limit_in_search_url(search_url, 1000)
    check_interval = 600
    repo = CarListingRepository("public/known_listings.json", "public/good_cars.json")
    crawler = EncarCrawler()
    filter = CarConditionFilter()
    
    monitor = EncarMonitor(search_url, check_interval, repo, crawler, filter)
    monitor.run() 