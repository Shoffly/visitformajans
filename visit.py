import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from datetime import datetime
from google.cloud import bigquery

# Set page config
st.set_page_config(
    page_title="نموذج زيارة تاجر السيارات",
    page_icon="🚗",
    layout="wide"
)


# Function to load dealer data from BigQuery
@st.cache_data(ttl=600)  # Cache data for 10 minutes
def load_dealers():
    try:
        # Get credentials for BigQuery
        try:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["service_account"]
            )
        except (KeyError, FileNotFoundError):
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    'service_account.json'
                )
            except FileNotFoundError:
                st.error("No credentials found for BigQuery access")
                return [], {}

        # Create BigQuery client
        client = bigquery.Client(credentials=credentials)

        # Query to get dealers
        query = """
        SELECT DISTINCT dealer_code, dealer_name
        FROM `pricing-338819.ajans_dealers.dealers`
        WHERE dealer_code IS NOT NULL AND dealer_name IS NOT NULL
        ORDER BY dealer_name
        """

        # Execute query
        dealers_data = client.query(query).to_dataframe()

        # Convert to list of dicts for compatibility
        dealers_list = dealers_data.to_dict('records')

        # Create dealer dictionary
        dealers_dict = dict(zip(dealers_data['dealer_code'], dealers_data['dealer_name']))

        return dealers_list, dealers_dict

    except Exception as e:
        st.error(f"خطأ في تحميل بيانات التجار: {str(e)}")
        return [], {}


# Function to submit form data to Google Sheets
def submit_form_data(form_data):
    try:
        # Get credentials for BigQuery
        try:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["service_account"]
            )
        except (KeyError, FileNotFoundError):
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    'service_account.json'
                )
            except FileNotFoundError:
                st.error("No credentials found for BigQuery access")
                return False, "Error: No credentials found"

        # Create BigQuery client
        client = bigquery.Client(credentials=credentials)

        # Prepare the query
        query = """
        INSERT INTO `pricing-338819.wholesale_test.visit_form_1`
        (Date, Dealer_name, dealer_spoc, Dealer_code, visit_type, visitor,
         app_overview, flash_sale, showroom_performance, swift_adoption,
         direct_lending, car_sharing, d2c_adoption, postive_feedback,
         negative_feedback, Next_actions, action_owner, action_date,
         interested_in_visit, benefit_of_visit, next_visit_date,
         perfered_com_channel)
        VALUES
        (@date, @dealer_name, @dealer_spoc, @dealer_code, @visit_type, @visitor,
         @app_overview, @flash_sale, @showroom_performance, @swift_adoption,
         @direct_lending, @car_sharing, @d2c_adoption, @postive_feedback,
         @negative_feedback, @next_actions, @action_owner, @action_date,
         @interested_in_visit, @benefit_of_visit, @next_visit_date,
         @perfered_com_channel)
        """

        # Configure query parameters
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("date", "DATE", form_data['date']),
                bigquery.ScalarQueryParameter("dealer_name", "STRING", form_data['dealer_name']),
                bigquery.ScalarQueryParameter("dealer_spoc", "STRING", form_data['dealer_spoc']),
                bigquery.ScalarQueryParameter("dealer_code", "STRING", form_data['dealer_code']),
                bigquery.ScalarQueryParameter("visit_type", "STRING", form_data['visit_type']),
                bigquery.ScalarQueryParameter("visitor", "STRING", form_data['visited_by']),
                bigquery.ScalarQueryParameter("app_overview", "STRING", form_data['app_overview']),
                bigquery.ScalarQueryParameter("flash_sale", "STRING", form_data['flash_sale']),
                bigquery.ScalarQueryParameter("showroom_performance", "STRING", form_data['showroom_performance']),
                bigquery.ScalarQueryParameter("swift_adoption", "STRING", form_data['swift_adoption']),
                bigquery.ScalarQueryParameter("direct_lending", "STRING", form_data['direct_lending']),
                bigquery.ScalarQueryParameter("car_sharing", "STRING", form_data['car_sharing']),
                bigquery.ScalarQueryParameter("d2c_adoption", "STRING", form_data['d2c_adoption']),
                bigquery.ScalarQueryParameter("postive_feedback", "STRING", form_data['postive_feedback']),
                bigquery.ScalarQueryParameter("negative_feedback", "STRING", form_data['negative_feedback']),
                bigquery.ScalarQueryParameter("next_actions", "STRING", form_data['next_actions']),
                bigquery.ScalarQueryParameter("action_owner", "STRING", form_data['action_owner']),
                bigquery.ScalarQueryParameter("action_date", "DATE", form_data['action_date']),
                bigquery.ScalarQueryParameter("interested_in_visit", "BOOL", form_data['interested_in_visit']),
                bigquery.ScalarQueryParameter("benefit_of_visit", "STRING", form_data['benefit_of_visit']),
                bigquery.ScalarQueryParameter("next_visit_date", "DATE", form_data['next_visit_date']),
                bigquery.ScalarQueryParameter("perfered_com_channel", "STRING", form_data['perfered_com_channel'])
            ]
        )

        # Execute the query
        query_job = client.query(query, job_config=job_config)
        query_job.result()  # Wait for the query to complete

        return True, "تم تقديم النموذج بنجاح!"

    except Exception as e:
        return False, f"خطأ في تقديم النموذج: {str(e)}"


# Main app
def main():
    st.title("🚗 نموذج زيارة تجار ")

    # Load dealer data
    with st.spinner("جاري تحميل بيانات التجار..."):
        dealers_data, dealers_dict = load_dealers()

    if not dealers_data:
        st.warning("لا توجد بيانات متاحة للتجار. يرجى التحقق من جدول Google الخاص بك.")
        return

    # Create form
    with st.form("dealer_visit_form"):
        # General Information Section - expanded by default
        with st.expander("بيانات عامة", expanded=True):
            # Get current date automatically
            visit_date = datetime.now().date()
            st.info(f"تاريخ الزيارة: {visit_date.strftime('%Y-%m-%d')}")

            # Dealer selection
            dealer_options = [(dealer['dealer_code'], dealer['dealer_name']) for dealer in dealers_data]
            dealer_codes = [code for code, _ in dealer_options]
            dealer_names = [name for _, name in dealer_options]

            selected_dealer_index = st.selectbox(
                "اسم المعرض",
                options=range(len(dealer_options)),
                format_func=lambda i: dealer_options[i][1]
            )
            selected_dealer_code = dealer_codes[selected_dealer_index]
            selected_dealer_name = dealer_names[selected_dealer_index]

            # Dealer SPOC
            dealer_spoc = st.text_input("اسم التاجر")

            # Visit type
            visit_type = st.selectbox(
                "نوع الزيارة",
                options=["زيارة أولى", "زيارة متابعة", "زيارة حل مشكلة"]
            )

            # Visited by
            visited_by = st.selectbox(
                "تمت الزيارة بواسطة",
                options=["Sadek", "Mostafa", "Mai", "Mohamed", "Yousif", "Mamdouh"]
            )

        # Main Discussion Points Section - closed by default
        with st.expander("نقاط الحوار الرئيسية", expanded=False):
            # App overview
            app_overview = st.text_area("أداء التطبيق بشكل عام")

            # Flash sale
            flash_sale = st.text_area("شراء السيارات في ال ٧٢ ساعة")

            # Showroom performance
            showroom_performance = st.text_area("العرض في المعرض")

            # Swift adoption
            swift_adoption = st.text_area("تمويل Swift للعملاء")

            # Direct lending
            direct_lending = st.text_area("الإقراض المباشر Direct Lending")

            # Car sharing
            car_sharing = st.text_area("مشاركة العربيات من الابليكشن للعملاء")

            # D2C adoption
            d2c_adoption = st.text_area("موقع الاجانص D2C")

            # Positive feedback
            positive_feedback = st.text_area("اكتر حاجة ايجابية في الاجانص")

            # Negative feedback
            negative_feedback = st.text_area("اكتر حاجة سلبية في الاجانص")

        # Actionable Results Section - closed by default
        with st.expander("نتائج قابلة للتنفيذ", expanded=False):
            # Next actions
            next_actions = st.text_area("الإجراء المتفق عليه")

            # Action owner
            action_owner = st.text_input("مسؤول التنفيذ")

            # Action date
            action_date = st.date_input("الموعد المستهدف")

        # Visit Evaluation Section - closed by default
        with st.expander("تقييم الزيارة", expanded=False):
            # Dealer interest
            interested_in_visit = st.selectbox(
                "مدى تفاعل التاجر",
                options=["متفاعل", "غير متفاعل"],
                format_func=lambda x: "نعم" if x == "متفاعل" else "لا"
            )

            # Visit benefit
            benefit_of_visit = st.selectbox(
                "الاستفادة من الزيارة",
                options=["عالية", "متوسطة", "منخفضة"]
            )

        # Follow-up Plan Section - closed by default
        with st.expander("خطة المتابعة", expanded=False):
            # Next visit date
            next_visit_date = st.date_input("تاريخ الزيارة القادمة")

            # Preferred communication channel
            preferred_channel = st.selectbox(
                "قناة التواصل المفضلة",
                options=["WhatsApp", "Phone Call", "Email"]
            )

        # Submit button
        submit_button = st.form_submit_button("تقديم النموذج")

        if submit_button:
            # Prepare form data
            form_data = {
                'date': visit_date,
                'dealer_name': selected_dealer_name,
                'dealer_spoc': dealer_spoc,
                'dealer_code': selected_dealer_code,
                'visit_type': visit_type,
                'visited_by': visited_by,
                'app_overview': app_overview,
                'flash_sale': flash_sale,
                'showroom_performance': showroom_performance,
                'swift_adoption': swift_adoption,
                'direct_lending': direct_lending,
                'car_sharing': car_sharing,
                'd2c_adoption': d2c_adoption,
                'postive_feedback': positive_feedback,
                'negative_feedback': negative_feedback,
                'next_actions': next_actions,
                'action_owner': action_owner,
                'action_date': action_date,
                'interested_in_visit': interested_in_visit == "متفاعل",
                'benefit_of_visit': benefit_of_visit,
                'next_visit_date': next_visit_date,
                'perfered_com_channel': preferred_channel
            }

            # Submit form data
            success, message = submit_form_data(form_data)

            if success:
                st.success(message)
                st.balloons()
            else:
                st.error(message)


if __name__ == "__main__":
    # Set Arabic RTL layout
    st.markdown("""
    <style>
    body {
        direction: rtl;
        text-align: right;
    }
    .stTextInput, .stTextArea, .stSelectbox, .stMultiselect {
        direction: rtl;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

    main()
