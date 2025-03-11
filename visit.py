import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="نموذج زيارة تاجر السيارات",
    page_icon="🚗",
    layout="wide"
)


# Function to load dealer data from Google Sheets
@st.cache_data(ttl=600)  # Cache data for 10 minutes
def load_dealers():
    try:
        # Set up Google Sheets API
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        # Try using service account file first
        try:
            credentials = Credentials.from_service_account_file('sheet_access.json', scopes=scopes)
        except:
            # If file not found, try using secrets
            credentials_dict = st.secrets["gcp_service_account"]
            credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)

        gc = gspread.authorize(credentials)

        # Open the spreadsheet
        spreadsheet = gc.open('visit form - data')

        # Get the dealers tab for dealer names
        dealers_sheet = spreadsheet.worksheet('dealers')
        dealer_headers = ['dealer_code', 'dealer_name']
        dealers_data = dealers_sheet.get_all_records(expected_headers=dealer_headers)

        # Create a dictionary mapping dealer_code to dealer_name
        dealers_dict = {dealer['dealer_code']: dealer['dealer_name'] for dealer in dealers_data}

        return dealers_data, dealers_dict

    except Exception as e:
        st.error(f"خطأ في تحميل بيانات التجار: {str(e)}")
        return [], {}


# Function to submit form data to Google Sheets
def submit_form_data(form_data):
    try:
        # Set up Google Sheets API
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        # Try using service account file first
        try:
            credentials = Credentials.from_service_account_file('sheet_access.json', scopes=scopes)
        except:
            # If file not found, try using secrets
            credentials_dict = st.secrets["gcp_service_account"]
            credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)

        gc = gspread.authorize(credentials)

        # Open the spreadsheet
        spreadsheet = gc.open('visit form - data')

        # Get the responses tab
        responses_sheet = spreadsheet.worksheet('responses')

        # Append the form data to the responses sheet
        responses_sheet.append_row([
            form_data['submitted_datetime'],
            form_data['dealer'],
            form_data['purpose'],
            form_data['showroom'],
            form_data['swift'],
            form_data['lending'],
            form_data['buy_now'],
            form_data['problems'],
            form_data['positives'],
            form_data['requests'],
            form_data['hatla2ee_link'],
            form_data['dubizzle_link'],
            form_data['showroom_capacity'],
            form_data['dealer_code'],
            form_data['issues']
        ])

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
        st.subheader("معلومات الزيارة")

        # Dealer selection
        dealer_options = [(dealer['dealer_code'], dealer['dealer_name']) for dealer in dealers_data]
        dealer_codes = [code for code, _ in dealer_options]
        dealer_names = [name for _, name in dealer_options]

        selected_dealer_index = st.selectbox(
            "اختر التاجر *",
            options=range(len(dealer_options)),
            format_func=lambda i: dealer_options[i][1]
        )
        selected_dealer_code = dealer_codes[selected_dealer_index]
        selected_dealer_name = dealer_names[selected_dealer_index]

        # Purpose of visit (required)
        purpose = st.text_area("الغرض من الزيارة ", help="يرجى وصف سبب زيارتك لهذا التاجر")

        # Yes/No questions
        st.subheader("أسئلة نعم/لا")

        col1, col2 = st.columns(2)
        with col1:
            showroom_question = st.radio(
                "تم اعلام التاجر عن العرض في معرضه؟ *",
                options=["نعم", "لا"],
                horizontal=True
            )

            swift_question = st.radio(
                "تم اعلام التاجر عن سويفت؟ *",
                options=["نعم", "لا"],
                horizontal=True
            )

        with col2:
            lending_question = st.radio(
                "تم اعلام التاجر عن التمويل المباشر؟ *",
                options=["نعم", "لا"],
                horizontal=True
            )

            buy_now_question = st.radio(
                "تم اعلام التاجر عن تحديث اشتري الآن؟ *",
                options=["نعم", "لا"],
                horizontal=True
            )

        # Issues multi-select
        issues_options = [
            "الأسعار",
            "مجموعة السيارات",
            "عرض بمعرضه",
            "سويفت",
            "التمويل المباشر",
            "لا يوجد"
        ]

        issues = st.multiselect(
            "ما هي المشاكل التي يواجهها التاجر؟ *",
            options=issues_options,
            help="يمكنك اختيار أكثر من خيار"
        )

        # Problems encountered (required)
        problems = st.text_area("مشاكل التاجر *", help="يرجى وصف أي مشاكل تمت مواجهتها أثناء الزيارة")

        # Positive aspects (required)
        positives = st.text_area("الإيجابيات *", help="يرجى وصف الجوانب الإيجابية التي لاحظتها أثناء الزيارة")

        # Optional fields
        st.subheader("معلومات إضافية (اختيارية)")

        # Requests
        requests = st.text_area("الطلبات", help="أي طلبات من التاجر")

        # Links
        col1, col2 = st.columns(2)
        with col1:
            hatla2ee_link = st.text_input("رابط Hatla2ee", help="أدخل رابط صفحة التاجر على Hatla2ee")
        with col2:
            dubizzle_link = st.text_input("رابط Dubizzle", help="أدخل رابط صفحة التاجر على Dubizzle")

        # Showroom capacity
        showroom_capacity = st.number_input("سعة صالة العرض", min_value=0, help="عدد السيارات التي يمكن عرضها")

        # Submit button
        submit_button = st.form_submit_button("تقديم النموذج")

        if submit_button:
            # Validate required fields
            if not problems or not positives or not issues:
                st.error("يرجى ملء جميع الحقول المطلوبة (المشار إليها بعلامة *)")
            else:
                # Convert yes/no to boolean strings for Google Sheets
                showroom_value = "Yes" if showroom_question == "نعم" else "No"
                swift_value = "Yes" if swift_question == "نعم" else "No"
                lending_value = "Yes" if lending_question == "نعم" else "No"
                buy_now_value = "Yes" if buy_now_question == "نعم" else "No"

                # Join issues with comma for Google Sheets
                issues_value = ", ".join(issues)

                # Prepare form data
                form_data = {
                    'submitted_datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'dealer': selected_dealer_name,
                    'dealer_code': selected_dealer_code,
                    'purpose': purpose,
                    'showroom': showroom_value,
                    'swift': swift_value,
                    'lending': lending_value,
                    'buy_now': buy_now_value,
                    'problems': problems,
                    'positives': positives,
                    'requests': requests,
                    'hatla2ee_link': hatla2ee_link,
                    'dubizzle_link': dubizzle_link,
                    'showroom_capacity': showroom_capacity,
                    'issues': issues_value
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
