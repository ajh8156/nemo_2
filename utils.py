import re

def format_price(amount_manwon: int) -> str:
    """
    금액(만원 단위)을 한글 읽기 편한 형식으로 변환
    - 10000 이상: X억 Y,ZZZ만원
    - 10000 미만: X,XXX만원
    """
    if not amount_manwon or amount_manwon == 0:
        return "-"
    
    if amount_manwon >= 10000:
        uk = amount_manwon // 10000
        man = amount_manwon % 10000
        if man == 0:
            return f"{uk}억원"
        return f"{uk}억 {man:,}만원"
    
    return f"{amount_manwon:,}만원"

def parse_subway(text: str):
    """
    "역명, 도보 N분" 형식의 문자열에서 역명과 도보 분수를 추출
    예: "이촌(국립중앙박물관)역, 도보 6분" -> ("이촌(국립중앙박물관)역", 6)
    """
    if not text or not isinstance(text, str):
        return "-", 99 # 기본값
    
    # 역명 추출
    station_match = text.split(",")[0].strip()
    
    # 도보 분수 추출
    walk_match = re.search(r'도보\s*(\d+)분', text)
    walk_minutes = int(walk_match.group(1)) if walk_match else 99
    
    return station_match, walk_minutes
