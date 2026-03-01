import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# 페이지 설정
st.set_page_config(
    page_title="Nemo 매물 분석 대시보드",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (Premium Look)
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .property-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
    .title-text {
        color: #1e293b;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    db_path = "nemo/data/nemo.db"
    if not os.path.exists(db_path):
        return pd.DataFrame()
    
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM store_items"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # 데이터 전처리
    if not df.empty:
        # 보증금, 월세 단위 변환 (만원 단위 유지하거나 필요시 억 단위 병기)
        df['deposit_display'] = df['deposit'].apply(lambda x: f"{x//10000}억 {x%10000}만" if x >= 10000 else f"{x}만")
        df['monthly_rent_display'] = df['monthly_rent'].apply(lambda x: f"{x}만")
        
    return df

def main():
    st.title("🏠 Nemo 상가/사무실 매물 대시보드")
    st.markdown("수집된 매물 데이터를 분석하고 상세 정보를 확인합니다.")

    df = load_data()

    if df.empty:
        st.warning("데이터베이스에 매물이 없습니다. 스크레이퍼를 먼저 실행해주세요.")
        return

    # 사이드바 필터
    st.sidebar.header("🔍 필터")
    
    regions = ["전체"] + sorted(df['standard_region'].unique().tolist())
    selected_region = st.sidebar.selectbox("지역 선택", regions)
    
    biz_types = ["전체"] + sorted(df['business_large_code_name'].unique().tolist())
    selected_biz = st.sidebar.selectbox("업종 선택", biz_types)
    
    # 필터 적용
    filtered_df = df.copy()
    if selected_region != "전체":
        filtered_df = filtered_df[filtered_df['standard_region'] == selected_region]
    if selected_biz != "전체":
        filtered_df = filtered_df[filtered_df['business_large_code_name'] == selected_biz]

    # 주요 지표 (KPI)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 매물 수", f"{len(filtered_df)}건")
    with col2:
        avg_deposit = filtered_df['deposit'].mean()
        st.metric("평균 보증금", f"{avg_deposit:,.0f}만원")
    with col3:
        avg_rent = filtered_df['monthly_rent'].mean()
        st.metric("평균 월세", f"{avg_rent:,.0f}만원")
    with col4:
        avg_premium = filtered_df['premium'].mean()
        st.metric("평균 권리금", f"{avg_premium:,.0f}만원")

    st.divider()

    # 시각화 영역
    tab1, tab2, tab3 = st.tabs(["📊 시장 분석", "📋 매물 목록", "🔍 상세 보기"])

    with tab1:
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("📍 지역별 매물 분포")
            region_counts = filtered_df['standard_region'].value_counts().reset_index()
            region_counts.columns = ['지역', '매물수']
            fig_region = px.bar(region_counts, x='지역', y='매물수', 
                               color='매물수', color_continuous_scale='Viridis',
                               template='plotly_white')
            st.plotly_chart(fig_region, use_container_width=True)
            
        with c2:
            st.subheader("💰 보증금 vs 월세 상관관계")
            fig_scatter = px.scatter(filtered_df, x='deposit', y='monthly_rent',
                                    color='business_large_code_name',
                                    size='size', hover_name='title',
                                    labels={'deposit': '보증금(만원)', 'monthly_rent': '월세(만원)'},
                                    template='plotly_white')
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.subheader("🏢 업종별 평균 가격 정보")
        biz_analysis = filtered_df.groupby('business_large_code_name').agg({
            'deposit': 'mean',
            'monthly_rent': 'mean',
            'premium': 'mean'
        }).reset_index()
        
        fig_biz = go.Figure()
        fig_biz.add_trace(go.Bar(name='보증금/10', x=biz_analysis['business_large_code_name'], y=biz_analysis['deposit']/10))
        fig_biz.add_trace(go.Bar(name='월세', x=biz_analysis['business_large_code_name'], y=biz_analysis['monthly_rent']))
        fig_biz.add_trace(go.Bar(name='권리금', x=biz_analysis['business_large_code_name'], y=biz_analysis['premium']))
        fig_biz.update_layout(barmode='group', template='plotly_white', title="업종별 평균 가격 비교 (보증금은 1/10 스케일)")
        st.plotly_chart(fig_biz, use_container_width=True)

    with tab2:
        st.subheader("매물 데이터 시트")
        display_cols = ['article_no', 'title', 'standard_region', 'business_large_code_name', 
                       'deposit', 'monthly_rent', 'premium', 'size', 'floor']
        st.dataframe(filtered_df[display_cols], use_container_width=True)

    with tab3:
        st.subheader("선택 매물 상세 정보")
        selected_article = st.selectbox("상세 정보를 확인할 매물을 선택하세요", 
                                       options=filtered_df['article_no'].tolist(),
                                       format_func=lambda x: f"[{x}] {filtered_df[filtered_df['article_no']==x]['title'].values[0]}")
        
        if selected_article:
            item = filtered_df[filtered_df['article_no'] == selected_article].iloc[0]
            raw_data = json.loads(item['raw_json'])
            
            detail_col1, detail_col2 = st.columns([1, 2])
            
            with detail_col1:
                # 사진 표시
                if raw_data.get('previewPhotoUrl'):
                    st.image(raw_data['previewPhotoUrl'], use_container_width=True, caption="매물 미리보기")
                
                if raw_data.get('smallPhotoUrls'):
                    st.write("추가 사진")
                    cols = st.columns(3)
                    for idx, img_url in enumerate(raw_data['smallPhotoUrls'][:6]):
                        cols[idx % 3].image(img_url, use_container_width=True)
            
            with detail_col2:
                st.markdown(f"### {item['title']}")
                st.markdown(f"**📍 위치:** {item['standard_region']} ({item['near_subway_station']})")
                st.markdown(f"**🏢 분류:** {item['business_large_code_name']} > {item['business_middle_code_name']}")
                
                price_col1, price_col2, price_col3 = st.columns(3)
                price_col1.metric("보증금", item['deposit_display'])
                price_col2.metric("월세", item['monthly_rent_display'])
                price_col3.metric("권리금", f"{item['premium']}만")
                
                st.markdown("---")
                info_col1, info_col2 = st.columns(2)
                info_col1.write(f"**전용 면적:** {item['size']}㎡")
                info_col1.write(f"**층수:** {item['floor']}층 (총 {item['ground_floor']}층)")
                info_col2.write(f"**조회수:** {item['view_count']}")
                info_col2.write(f"**관심 등록:** {item['favorite_count']}")
                
                st.markdown("**📅 등록/수정일**")
                st.caption(f"최초 등록: {item['created_date_utc']} | 마지막 수정: {item['edited_date_utc']}")

if __name__ == "__main__":
    main()
