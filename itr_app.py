import streamlit as st
import pandas as pd
from datetime import date, timedelta
from google_sheet_functions import (
    load_client_data,
    save_dataframe,
    add_history,
    load_history_data,
    add_client_row,
    add_receipt_history,
    load_receipt_history
)

from reportlab.pdfgen import canvas
from io import BytesIO

def generate_invoice_pdf(
        client_name,
        invoice_no,
        amount
    ):
    
        buffer = BytesIO()
    
        pdf = canvas.Canvas(buffer)
    
        pdf.drawString(
            100,
            800,
            "S K Consultancy Services"
        )
    
        pdf.drawString(
            100,
            770,
            f"Invoice : {invoice_no}"
        )
    
        pdf.drawString(
            100,
            740,
            f"Client : {client_name}"
        )
    
        pdf.drawString(
            100,
            710,
            f"Amount : ₹{amount:,.0f}"
        )
    
        pdf.save()
    
        buffer.seek(0)
    
        return buffer

st.set_page_config(
    page_title="ITR Client Tracker",
    layout="wide"
)

# =====================
# LOGIN
# =====================

# 1. Initialize session state to track login status
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 2. Create a placeholder for the login form
login_placeholder = st.empty()

if not st.session_state.logged_in:
    with login_placeholder.container():
        st.header("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            users = st.secrets["users"]
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                # Clear the login form immediately
                login_placeholder.empty()
                st.rerun()
            else:
                st.error("Invalid username or password")

# 3. Show content only after login
if st.session_state.logged_in:
    st.success(f"Welcome to CMS, {st.session_state.username}!")
    

menu = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Work In Progress",
        "Client List",
        "Edit Client",
        "Add Client",
        "Follow-Ups",
        "Billing",
        "Receipt History",
        "Fee Recovery",
        "Update History"
    ]
)

# =====================
# LOAD DATA
# =====================

df = load_client_data()

# =====================
# DASHBOARD
# =====================

if menu == "Dashboard":

    st.title("📋 ITR Client Management System")

    active_df = df[
        df["Status of Work"]
        .astype(str)
        .str.strip()
        .str.lower() != "inactive"
    ]

    total_clients = len(active_df)

    pending_returns = len(
        active_df[
            ~active_df["Status of Work"]
            .astype(str)
            .isin(
                [
                    "Filed",
                    "e-Verified",
                    "Completed"
                ]
            )
        ]
    )

    filed_returns = len(
        active_df[
            active_df["Status of Work"]
            .astype(str)
            .str.strip()
            == "Filed"
        ]
    )

    everified_returns = len(
        active_df[
            active_df["Status of Work"]
            .astype(str)
            .str.strip()
            == "e-Verified"
        ]
    )

    inactive_clients = len(
        df[
            df["Status of Work"]
            .astype(str)
            .str.strip()
            .str.lower()
            == "inactive"
        ]
    )

    c1,c2,c3,c4,c5 = st.columns(5)

    c1.metric("Active Clients", total_clients)
    c2.metric("Pending", pending_returns)
    c3.metric("Filed", filed_returns)
    c4.metric("e-Verified", everified_returns)
    c5.metric("Inactive", inactive_clients)

    st.divider()

    st.subheader("👨‍💼 Work Allocation")

    if "Assigned To" in df.columns:
        allocation = (
            df.groupby("Assigned To")
            .size()
            .reset_index(name="Clients")
            .sort_values(
                "Clients",
                ascending=False
            )
        )
        st.dataframe(
            allocation,
            use_container_width=True,
            hide_index=True
        )
    st.divider()

    st.subheader("💰 Fee Dashboard")

    total_proposed = pd.to_numeric(
        df["Fee Proposed FY 2025 26 (₹)"],
        errors="coerce"
    ).fillna(0).sum()

    total_received = pd.to_numeric(
        df["Fee Reciept FY 2025 26 (₹)"],
        errors="coerce"
    ).fillna(0).sum()

    total_due = pd.to_numeric(
        df["Amount Due"],
        errors="coerce"
    ).fillna(0).sum()

    f1, f2, f3 = st.columns(3)

    f1.metric(
        "💰 Fee Proposed",
        f"₹{total_proposed:,.0f}"
    )

    f2.metric(
        "✅ Fee Received",
        f"₹{total_received:,.0f}"
    )

    f3.metric(
        "⚠️ Outstanding",
        f"₹{total_due:,.0f}"
    )

    st.divider()
    
    st.subheader("📊 Active Work Summary")

    wip_df = df[
        ~df["Status of Work"].isin(
            [
                "Not Started",
                "Completed",
                "Inactive"
            ]
        )
    ]
    
    status_summary = (
        wip_df.groupby(
            "Status of Work"
        )
        .size()
        .reset_index(name="Count")
        .sort_values(
            "Count",
            ascending=False
        )
    )
    
    st.dataframe(
        status_summary,
        use_container_width=True,
        hide_index=True
    )

    st.divider()
    st.subheader("📌 Work In Progress")
    
    wip_status_exclude = [
        "Not Started",
        "Completed",
        "Inactive"
    ]
    
    wip_df = df[
        ~df["Status of Work"].isin(
            wip_status_exclude
        )
    ]
    
    st.metric(
        "Active Cases",
        len(wip_df)
    )
    
    st.dataframe(
        wip_df[
            [
                "Client Name",
                "Assigned To",
                "Status of Work",
                "Next Follow Up"
            ]
        ],
        use_container_width=True
    )

# =====================
# CLIENT LIST
# =====================

elif menu == "Client List":

    st.header("📄 Client List")

    search = st.text_input(
        "Search ID /Name / PAN / Mobile"
    )

    filtered_df = df.copy()

    if search:

        filtered_df = filtered_df[
            filtered_df.astype(str)
            .apply(
                lambda row:
                row.str.contains(
                    search,
                    case=False,
                    na=False
                ).any(),
                axis=1
            )
        ]

    st.dataframe(
        filtered_df,
        use_container_width=True
    )


# =====================

# EDIT CLIENT

# =====================

elif menu == "Edit Client":

    st.header("✏️ Edit Client")
    
    client = st.selectbox(
        "Select Client",
        sorted(df["Client Name"].dropna().unique())
    )
    
    row_index = df[
        df["Client Name"] == client
    ].index[0]
    
    row = df.loc[row_index]
    
    # =====================
    # CLIENT PROFILE
    # =====================
    
    st.subheader("📋 Client Profile")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.write("**PAN:**", row.get("PAN", ""))
        st.write("**Mobile:**", row.get("Mobile", ""))
        st.write("**Email:**", row.get("Email", ""))
    
    with c2:
        st.write("**Assigned To:**", row.get("Assigned To", ""))
        st.write("**Status:**", row.get("Status of Work", ""))
        st.write("**Client Source:**", row.get("Client Source", ""))
    
    with c3:
        st.write(
            "**Fee Proposed:** ₹",
            row.get("Fee Proposed FY 2025 26 (₹)", 0)
        )
    
        st.write(
            "**Fee Received:** ₹",
            row.get("Fee Reciept FY 2025 26 (₹)", 0)
        )
    
        st.write(
            "**Amount Due:** ₹",
            row.get("Amount Due", 0)
        )
    
    st.divider()
    
    # =====================
    # EDIT FORM
    # =====================
    
    status_options = [
        "Documents Awaited",
        "Documents Received",
        "Under Preparation",
        "Query Raised",
        "Ready for Filing",
        "Filed",
        "e-Verified",
        "Bill Pending",
        "Completed",
        "Inactive"
    ]
    
    assigned_options = [
        "Suraj",
        "Sujith",
        "Vandana",
        "Vidya",
        "Srinivas"
    ]
    
    current_status = str(
        row.get("Status of Work", "")
    )
    
    status_index = (
        status_options.index(current_status)
        if current_status in status_options
        else 0
    )
    
    new_status = st.selectbox(
        "Status",
        status_options,
        index=status_index
    )
    
    current_assigned = str(
        row.get("Assigned To", "Suraj")
    )
    
    assigned_index = (
        assigned_options.index(current_assigned)
        if current_assigned in assigned_options
        else 0
    )
    
    assigned_to = st.selectbox(
        "Assigned To",
        assigned_options,
        index=assigned_index
    )
    
    proposed_fee = st.number_input(
        "Proposed Fee",
        min_value=0.0,
        value=float(
            pd.to_numeric(
                row.get(
                    "Fee Proposed FY 2025 26 (₹)",
                    0
                ),
                errors="coerce"
            )
        )
    )
    
    # =====================
    # FOLLOW UP DATE
    # =====================
    
    current_followup = pd.to_datetime(
        row.get("Next Follow Up", ""),
        errors="coerce",
        dayfirst=True
    )
    
    if pd.isna(current_followup):
        current_followup = date.today()
    else:
        current_followup = current_followup.date()
    
    next_followup = st.date_input(
        "Next Follow Up",
        value=current_followup
    )
    
    remarks = st.text_area(
        "Remarks",
        value=str(
            row.get(
                "Brief Status of Work",
                ""
            )
        ),
        height=120
    )
    
    # =====================
    # OLD VALUES
    # =====================
    
    old_status = str(
        row.get("Status of Work", "")
    )
    
    old_assigned = str(
        row.get("Assigned To", "")
    )
    
    old_remarks = str(
        row.get("Brief Status of Work", "")
    )
    
    # =====================
    # SAVE
    # =====================
    
    if st.button("💾 Save Changes"):
    
        df.at[
            row_index,
            "Status of Work"
        ] = str(new_status)
    
        df.at[
            row_index,
            "Assigned To"
        ] = str(assigned_to)
    
        df.at[
            row_index,
            "Brief Status of Work"
        ] = str(remarks)
    
        df.at[
            row_index,
            "Fee Proposed FY 2025 26 (₹)"
        ] = float(proposed_fee)
    
        # Auto clear follow-up for completed cases
    
        if new_status in [
            "Filed",
            "e-Verified",
            "Completed",
            "Inactive"
        ]:
    
            df.at[
                row_index,
                "Next Follow Up"
            ] = ""
    
        else:
    
            df.at[
                row_index,
                "Next Follow Up"
            ] = next_followup.strftime(
                "%d-%m-%Y"
            )
    
        save_dataframe(df)
    
        if old_status != new_status:
    
            add_history(
                logged_user,
                "",
                client,
                "Status",
                old_status,
                new_status
            )
    
        if old_assigned != assigned_to:
    
            add_history(
                logged_user,
                "",
                client,
                "Assigned To",
                old_assigned,
                assigned_to
            )
    
        if old_remarks != remarks:
    
            add_history(
                logged_user,
                "",
                client,
                "Remarks",
                old_remarks,
                remarks
            )
    
        st.success(
            "✅ Client Updated Successfully"
        )
    
        st.rerun()
        
# =====================
# ADD CLIENT
# =====================

elif menu == "Add Client":

    st.header("➕ Add Client")

    cname = st.text_input(
        "Client Name"
    )

    pan = st.text_input(
        "PAN"
    )

    mobile = st.text_input(
        "Mobile"
    )

    CSource = st.selectbox(
        "Client Source",
        [
            "SKCS",
            "Vidya K & Co., Chartered Accountants",
            "Ramesh Ramakrishnan",
            "Sriram",
            "Srinivas"
        ]
    )

    assigned = st.selectbox(
        "Assigned To",
        [
            "Suraj",
            "Sujith",
            "Vandana",
            "Vidya",
            "Srinivas"
        ]
    )
    
    cref = st.text_input(
        "Client Folder Reference"
    )
        # Generate Next Client ID
    st.write("Current rows:", len(df))
    if "Client ID" in df.columns:

        existing_ids = (
            df["Client ID"]
            .astype(str)
            .str.replace("SK", "", regex=False)
        )

        existing_ids = pd.to_numeric(
            existing_ids,
            errors="coerce"
        )

        last_id = existing_ids.max()

        if pd.isna(last_id):
            last_id = 0

        new_client_id = (
            "SK" +
            str(int(last_id) + 1).zfill(6)
        )

    else:

        new_client_id = "SK000001"

    st.text_input(
    "Client ID",
        value=new_client_id,
        disabled=True
    )
        
    if st.button("Add Client"):

        new_row = {}

        for col in df.columns:
            new_row[col] = ""

        new_row["Client Name"] = cname
        new_row["PAN"] = pan
        new_row["Mobile"] = mobile
        new_row["Assigned To"] = assigned
        new_row["Status of Work"] = "Documents Awaited"
        new_row["Client ID"] = new_client_id
        new_row["Client Folder Reference"] = cref
        new_row["Client Source"] = CSource
        
        add_client_row(new_row)

        st.success("Client Added Successfully")
        st.rerun()

# =====================
# FOLLOW UPS
# =====================

elif menu == "Follow-Ups":

    st.header("📞 Follow-Ups")

    if "Next Follow Up" in df.columns:

        temp = df.copy()

        temp["Next Follow Up"] = pd.to_datetime(
            temp["Next Follow Up"],
            errors="coerce",
            dayfirst=True
        )

        due = temp[
            (temp["Next Follow Up"].notna())
            &
            (temp["Next Follow Up"].dt.date <= date.today())
            &
            (~temp["Status of Work"].astype(str).isin(
                [
                    "Filed",
                    "e-Verified",
                    "Completed",
                    "Inactive"
                ]
            ))
        ]

        st.metric(
            "Due Follow Ups",
            len(due)
        )

        if len(due) > 0:

            st.dataframe(
                due[
                    [
                        c for c in [
                            "Client Name",
                            "Mobile",
                            "Assigned To",
                            "Status of Work",
                            "Next Follow Up"
                        ]
                        if c in due.columns
                    ]
                ],
                use_container_width=True
            )

            selected_client = st.selectbox(
                "Select Client",
                due["Client Name"].tolist()
            )

            c1, c2 = st.columns(2)

            with c1:

                if st.button("🗑️ Remove Follow Up"):

                    remove_index = df[
                        df["Client Name"] == selected_client
                    ].index[0]

                    df.at[
                        remove_index,
                        "Next Follow Up"
                    ] = ""

                    save_dataframe(df)

                    st.success(
                        f"Follow-up removed for {selected_client}"
                    )

                    st.rerun()

            with c2:

                if st.button("⏰ Snooze 7 Days"):

                    remove_index = df[
                        df["Client Name"] == selected_client
                    ].index[0]

                    new_date = (
                        date.today() + timedelta(days=7)
                    ).strftime("%d-%m-%Y")

                    df.at[
                        remove_index,
                        "Next Follow Up"
                    ] = new_date

                    save_dataframe(df)

                    st.success(
                        f"Follow-up postponed to {new_date}"
                    )

                    st.rerun()

        else:

            st.info(
                "No follow-ups due today."
            )

    else:

        st.warning(
            "Column 'Next Follow Up' not found."
        )

# =====================
# Update History
# =====================
elif menu == "Update History":

    st.header("📜 Update History")

    history_df = load_history_data()

    st.dataframe(
        history_df,
        use_container_width=True
    )

# =====================
# RECEIPT HISTORY
# =====================

elif menu == "Receipt History":

    st.header("🧾 Receipt History")

    receipt_df = load_receipt_history()

    st.dataframe(
        receipt_df,
        use_container_width=True
    )
    
# =====================
# Fee Recovery
# =====================
elif menu == "Fee Recovery":

    st.header(
        "💰 Fee Recovery"
    )

    recovery_df = df.copy()

    recovery_df["Amount Due"] = pd.to_numeric(
        recovery_df["Amount Due"],
        errors="coerce"
    ).fillna(0)

    recovery_df = recovery_df[
        recovery_df["Amount Due"] > 0
    ]

    total_due = (
        recovery_df["Amount Due"]
        .sum()
    )

    st.metric(
        "Total Outstanding",
        f"₹{total_due:,.0f}"
    )

    st.dataframe(
        recovery_df[
            [
                "Client Name",
                "Mobile",
                "Assigned To",
                "Amount Due"
            ]
        ],
        use_container_width=True
    )
    
# =====================
# BILLING
# =====================

elif menu == "Billing":

    st.header("💰 Billing & Collections")

    if "Invoice No" not in df.columns:
        df["Invoice No"] = ""

    if "Next Collection Follow Up" not in df.columns:
        df["Next Collection Follow Up"] = ""

    client = st.selectbox(
        "Select Client",
        sorted(df["Client Name"].dropna().unique())
    )

    row_index = df[
        df["Client Name"] == client
    ].index[0]

    row = df.loc[row_index]

    invoice_no = str(
        row.get(
            "Invoice No",
            ""
        )
    ).strip()

    if invoice_no == "":

        invoice_no = (
            "INV" +
            str(row_index + 1).zfill(6)
        )

    st.info(
        f"Invoice Number : {invoice_no}"
    )
    
    proposed = float(
        pd.to_numeric(
            row.get(
                "Fee Proposed FY 2025 26 (₹)",
                0
            ),
            errors="coerce"
        )
    )
    
    invoice_pdf = generate_invoice_pdf(
        client,
        invoice_no,
        proposed
    )
    
    st.download_button(
        "📄 Download Invoice",
        invoice_pdf,
        file_name=f"{invoice_no}.pdf"
    )
    received = float(
        pd.to_numeric(
            row.get(
                "Fee Reciept FY 2025 26 (₹)",
                0
            ),
            errors="coerce"
        )
    )

    due = proposed - received

    c1,c2,c3 = st.columns(3)

    c1.metric(
        "Proposed Fee",
        f"₹{proposed:,.0f}"
    )

    c2.metric(
        "Received",
        f"₹{received:,.0f}"
    )

    c3.metric(
        "Due",
        f"₹{due:,.0f}"
    )

    st.divider()

    payment = st.number_input(
        "Amount Received",
        min_value=0.0,
        step=100.0
    )

    payment_mode = st.selectbox(
        "Payment Mode",
        [
            "Cash",
            "UPI",
            "Bank Transfer",
            "Cheque"
        ]
    )

    collection_followup = st.date_input(
        "Next Collection Follow Up",
        value=date.today()
    )

    remarks = st.text_area(
        "Collection Remarks"
    )

    if st.button("💾 Save Payment"):

        received = received + payment

        due = proposed - received

        if due < 0:
            due = 0

        df.at[
            row_index,
            "Invoice No"
        ] = invoice_no

        df.at[
            row_index,
            "Fee Reciept FY 2025 26 (₹)"
        ] = received

        df.at[
            row_index,
            "Amount Due"
        ] = due

        df.at[
            row_index,
            "Last Collection Date"
        ] = date.today().strftime(
            "%d-%m-%Y"
        )

        df.at[
            row_index,
            "Next Collection Follow Up"
        ] = collection_followup.strftime(
            "%d-%m-%Y"
        )

        save_dataframe(df)

        add_receipt_history(
            row.get(
                "Client ID",
                ""
            ),
            client,
            invoice_no,
            payment,
            payment_mode,
            logged_user,
            remarks
        )

        st.success(
            "Payment Saved Successfully"
        )

        st.rerun()
    
# =====================
# BILLING
# =====================

elif menu == "Work In Progress":

    st.header("📌 Work In Progress")

    wip_df = df[
        ~df["Status of Work"].isin(
            [
                "Not Started",
                "Completed",
                "Inactive"
            ]
        )
    ]

    st.metric(
        "Total Active Cases",
        len(wip_df)
    )

    st.dataframe(
        wip_df,
        use_container_width=True
    )
