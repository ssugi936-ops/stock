import streamlit as st
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

load_dotenv()


def get_market_sum_data():
    """네이버 금융 시가총액 페이지에서 종목명과 주가 정보를 크롤링합니다."""
    url = "https://finance.naver.com/sise/sise_market_sum.naver"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return ""

    response.encoding = 'euc-kr'
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find("table", {"class": "type_2"})
    if not table:
        return ""

    rows = table.find_all("tr")
    stock_list = []

    for row in rows:
        title_td = row.find("a", class_="tltle")
        if title_td:
            name = title_td.text.strip()
            tds = row.find_all("td")
            if len(tds) > 6:
                current_price = tds[2].text.strip()
                change_rate = tds[4].text.strip()
                market_cap = tds[6].text.strip()
                stock_list.append(f"종목명: {name} | 현재가: {current_price}원 | 등락률: {change_rate} | 시가총액: {market_cap}억원")

    return "\n".join(stock_list)


def summarize_stock_data(stock_data_text):
    """LangChain과 OpenAI를 사용하여 수집된 종목 데이터를 요약합니다."""
    if not stock_data_text:
        return "요약할 데이터가 없습니다."

    model = ChatOpenAI(model="gpt-5.5")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 주식 시장 데이터를 분석하고 요약하는 금융 전문가입니다. 제공된 데이터를 바탕으로 현재 시장의 주요 특징을 요약해 주세요."),
        ("user", "다음은 네이버 금융 시가총액 상위 종목들의 데이터입니다. 이를 바탕으로 상위 종목들의 전반적인 흐름, 크게 상승하거나 하락한 종목, 시가총액 특징 등을 분석하여 깔끔하게 요약해 주세요.\n\n[주식 데이터]\n{stock_data}")
    ])

    output_parser = StrOutputParser()
    chain = prompt | model | output_parser
    return chain.invoke({"stock_data": stock_data_text})


st.set_page_config(page_title="네이버 시가총액 AI 요약", page_icon="📈")
st.title("네이버 금융 시가총액 AI 요약")
st.write("네이버 금융 시가총액 상위 종목 데이터를 크롤링하고 AI로 요약합니다.")

if st.button("데이터 가져오기 및 요약하기"):
    with st.spinner("네이버 금융에서 시가총액 데이터를 가져오는 중..."):
        market_data = get_market_sum_data()

    if not market_data:
        st.error("데이터를 가져오지 못했습니다. 소스 코드나 웹페이지 구조를 확인해 주세요.")
    else:
        stock_count = len(market_data.splitlines())
        st.success(f"총 {stock_count}개의 종목 정보를 가져왔습니다.")

        with st.expander("크롤링한 원본 데이터 보기"):
            st.text(market_data)

        with st.spinner("AI를 활용해 데이터를 요약하는 중..."):
            summary = summarize_stock_data(market_data)

        st.markdown("### AI 요약 결과")
        st.write(summary)
