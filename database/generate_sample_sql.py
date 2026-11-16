import random
from datetime import datetime, timedelta

def generate_sql():
    random.seed(42)

    # 1. Locations (18 distinct cities)
    locations = [
        ("Mumbai", "Maharashtra", "India", 19.0760, 72.8777),
        ("Delhi", "Delhi", "India", 28.7041, 77.1025),
        ("Bengaluru", "Karnataka", "India", 12.9716, 77.5946),
        ("Hyderabad", "Telangana", "India", 17.3850, 78.4867),
        ("Chennai", "Tamil Nadu", "India", 13.0827, 80.2707),
        ("Kolkata", "West Bengal", "India", 22.5726, 88.3639),
        ("Pune", "Maharashtra", "India", 18.5204, 73.8567),
        ("Ahmedabad", "Gujarat", "India", 23.0225, 72.5714),
        ("Jaipur", "Rajasthan", "India", 26.9124, 75.7873),
        ("Lucknow", "Uttar Pradesh", "India", 26.8467, 80.9462),
        ("Chandigarh", "Punjab", "India", 30.7333, 76.7794),
        ("Kochi", "Kerala", "India", 9.9312, 76.2673),
        ("Goa", "Goa", "India", 15.2993, 74.1240),
        ("Indore", "Madhya Pradesh", "India", 22.7196, 75.8577),
        ("Surat", "Gujarat", "India", 21.1702, 72.8311),
        ("Dubai", "Dubai", "United Arab Emirates", 25.2048, 55.2708),
        ("London", "Greater London", "United Kingdom", 51.5074, -0.1278),
        ("Singapore", "Central Region", "Singapore", 1.3521, 103.8198),
    ]

    # 2. Customers (60 customers)
    first_names = [
        "Aarav", "Aditi", "Rohan", "Pooja", "Vikram", "Ananya", "Rahul", "Sneha", "Karan", "Priya",
        "Arjun", "Neha", "Siddharth", "Divya", "Amit", "Kavita", "Rajesh", "Meera", "Suresh", "Ritu",
        "Deepak", "Shweta", "Gaurav", "Nisha", "Manoj", "Preeti", "Harsh", "Tanvi", "Alok", "Sunita",
        "Vikas", "Swati", "Nikhil", "Aarti", "Varun", "Isha", "Ravi", "Pallavi", "Sachin", "Jyoti",
        "Abhishek", "Smriti", "Manish", "Poonam", "Ashish", "Komal", "Dev", "Monika", "Yash", "Bhavna",
        "Tarun", "Payal", "Pranav", "Simran", "Hemant", "Radha", "Rohit", "Anjali", "Kunal", "Tanya"
    ]
    last_names = [
        "Sharma", "Verma", "Patel", "Reddy", "Nair", "Mehta", "Iyer", "Rao", "Gupta", "Singh",
        "Chopra", "Joshi", "Deshmukh", "Kulkarni", "Bhat", "Das", "Mukherjee", "Sen", "Pillai", "Choudhury",
        "Kapoor", "Bansal", "Agarwal", "Mishra", "Pandey", "Saxena", "Malhotra", "Khanna", "Bose", "Ghosh"
    ]

    customers = []
    for i in range(len(first_names)):
        fn = first_names[i]
        ln = last_names[i % len(last_names)]
        name = f"{fn} {ln}"
        email = f"{fn.lower()}.{ln.lower()}{i+10}@example.com"
        phone = f"+91 98{random.randint(10000000, 99999999)}"
        y = random.randint(1975, 2002)
        m = random.randint(1, 12)
        d = random.randint(1, 28)
        dob = f"{y:04d}-{m:02d}-{d:02d}"
        home_loc = locations[i % 12]  # local Indian cities
        city = home_loc[0]
        state = home_loc[1]
        status = "Active" if i < 55 else ("Suspended" if i == 56 else "Under Review")
        created_date = datetime(2025, random.randint(1, 11), random.randint(1, 28)).strftime("%Y-%m-%d %H:%M:%S")
        customers.append((i + 1, name, email, phone, dob, city, state, "India", status, created_date, i % 12 + 1))

    # 3. Accounts (75 accounts)
    accounts = []
    acc_id = 1
    for cust in customers:
        cid = cust[0]
        # Every customer has at least 1 account; first 15 have 2 accounts
        num_accs = 2 if cid <= 15 else 1
        for a_idx in range(num_accs):
            acc_num = f"SBIN{cid:04d}{a_idx+1:02d}{random.randint(1000, 9999)}"
            acc_type = "Savings" if a_idx == 0 else ("Credit Card" if cid % 2 == 0 else "Current")
            balance = round(random.uniform(15000, 450000), 2)
            opened = (datetime(2025, 1, 1) + timedelta(days=random.randint(0, 300))).strftime("%Y-%m-%d")
            accounts.append((acc_id, cid, acc_num, acc_type, balance, "Active", opened))
            acc_id += 1

    # 4. Devices (100 devices)
    devices = []
    dev_models = [
        ("Apple iPhone 15 Pro", "Mobile", "iOS 17"),
        ("Apple iPhone 14", "Mobile", "iOS 16"),
        ("Samsung Galaxy S24 Ultra", "Mobile", "Android 14"),
        ("Samsung Galaxy A54", "Mobile", "Android 13"),
        ("Google Pixel 8", "Mobile", "Android 14"),
        ("OnePlus 12", "Mobile", "Android 14"),
        ("MacBook Pro M2", "Desktop", "macOS Sonoma"),
        ("Dell XPS 15", "Desktop", "Windows 11"),
        ("Lenovo ThinkPad X1", "Desktop", "Windows 11"),
        ("Apple iPad Air 5", "Tablet", "iPadOS 17"),
        ("POS Verifone V200c", "POS Terminal", "Embedded Linux")
    ]
    dev_id = 1
    for cust in customers:
        cid = cust[0]
        # Main trusted phone
        model, dtype, os_name = dev_models[cid % 6]
        f_used = (datetime(2025, 2, 1) + timedelta(days=random.randint(0, 100))).strftime("%Y-%m-%d %H:%M:%S")
        l_used = (datetime(2026, 8, 1) + timedelta(days=random.randint(0, 50))).strftime("%Y-%m-%d %H:%M:%S")
        devices.append((dev_id, cid, model, dtype, os_name, f_used, l_used, "Trusted"))
        dev_id += 1

        # Second device for 40 customers (trusted laptop or tablet)
        if cid <= 40:
            model2, dtype2, os_name2 = dev_models[6 + (cid % 4)]
            devices.append((dev_id, cid, model2, dtype2, os_name2, f_used, l_used, "Trusted"))
            dev_id += 1

    # Add deliberately Untrusted or Suspicious devices for fraud scenarios
    suspicious_dev_cids = [5, 8, 12, 18, 22, 27, 33, 41, 48, 53]
    for cid in suspicious_dev_cids:
        devices.append((
            dev_id, cid, "Unknown Tor Browser / Virtual Machine", "Desktop", "Linux (Untrusted)",
            "2026-09-15 02:10:00", "2026-09-15 02:15:00", "Untrusted"
        ))
        dev_id += 1

    # Map customer to accounts and devices
    cust_to_accs = {}
    for a in accounts:
        cust_to_accs.setdefault(a[1], []).append(a[0])

    cust_to_devs = {}
    for d in devices:
        cust_to_devs.setdefault(d[1], []).append(d)

    # 5. Transactions (600 transactions with rich patterns)
    merchants = [
        "Amazon India", "Flipkart", "Swiggy", "Zomato", "Uber India", "Ola Cabs",
        "MakeMyTrip", "BookMyShow", "Croma Electronics", "Reliance Digital",
        "BigBasket", "Blinkit", "Apollo Pharmacy", "Tanishq Jewellers", "Zara Retail",
        "Starbucks Coffee", "HPCL Fuel Station", "Indian Oil", "Apple Store BKC", "CryptoPay Global"
    ]
    methods = ["UPI", "Net Banking", "Credit Card", "Debit Card", "ATM", "Wire Transfer"]
    types = ["Debit", "Payment", "Transfer", "Withdrawal"]

    transactions = []
    base_time = datetime(2026, 7, 1, 9, 0, 0)
    tx_id = 1

    # Step 5a: Generate 420 Normal Baseline Transactions across all customers
    for cid in range(1, len(customers) + 1):
        c_accs = cust_to_accs[cid]
        c_devs = [d for d in cust_to_devs[cid] if d[7] == "Trusted"]
        c_home_loc_id = customers[cid - 1][10]

        # Each customer gets 7 to 11 baseline transactions over 2 months
        num_baseline = random.randint(7, 11)
        cur_date = base_time + timedelta(days=random.randint(0, 15))
        for _ in range(num_baseline):
            acc_id = random.choice(c_accs)
            amt = round(random.uniform(300, 6500), 2)
            method = random.choice(["UPI", "Debit Card", "Net Banking"])
            ttype = "Debit" if method != "UPI" else "Payment"
            # Normal daytime between 08:00 and 22:00
            hour = random.randint(8, 22)
            minute = random.randint(0, 59)
            tx_time = cur_date.replace(hour=hour, minute=minute)
            dev = random.choice(c_devs) if c_devs else None
            dev_id_val = dev[0] if dev else "NULL"
            merchant = random.choice(merchants[:16])

            transactions.append((
                tx_id, acc_id, amt, ttype, method,
                tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                c_home_loc_id, dev_id_val, "Completed", merchant, 0, "LOW"
            ))
            tx_id += 1
            cur_date += timedelta(days=random.randint(2, 6))

    # Step 5b: Scenario 1 - Unusually High Transaction (Rule 1)
    # Customers whose normal avg is ~₹2,500 suddenly spend ₹85,000 - ₹250,000
    for cid in [3, 7, 14, 25, 36, 47]:
        acc_id = cust_to_accs[cid][0]
        c_dev = [d for d in cust_to_devs[cid] if d[7] == "Trusted"][0]
        c_loc = customers[cid - 1][10]
        high_amt = round(random.uniform(95000, 320000), 2)
        tx_time = datetime(2026, 9, random.randint(1, 10), random.randint(10, 18), random.randint(10, 50))
        transactions.append((
            tx_id, acc_id, high_amt, "Transfer", "Net Banking",
            tx_time.strftime("%Y-%m-%d %H:%M:%S"),
            c_loc, c_dev[0], "Completed", "CryptoPay Global", 0, "LOW"
        ))
        tx_id += 1

    # Step 5c: Scenario 2 - New/Untrusted Device Anomaly (Rule 2)
    for cid in [5, 8, 12, 18, 22]:
        acc_id = cust_to_accs[cid][0]
        untrusted_dev = [d for d in cust_to_devs[cid] if d[7] == "Untrusted"][0]
        c_loc = customers[cid - 1][10]
        amt = round(random.uniform(8000, 24000), 2)
        tx_time = datetime(2026, 9, random.randint(12, 18), random.randint(11, 20), random.randint(10, 50))
        transactions.append((
            tx_id, acc_id, amt, "Payment", "Credit Card",
            tx_time.strftime("%Y-%m-%d %H:%M:%S"),
            c_loc, untrusted_dev[0], "Completed", "Electronics Superstore", 0, "LOW"
        ))
        tx_id += 1

    # Step 5d: Scenario 3 - Unusual Location (Rule 3)
    # Customers who only transact in Chennai/Delhi suddenly transact in Dubai/London/Singapore
    unusual_loc_ids = [16, 17, 18]  # Dubai, London, Singapore
    for idx, cid in enumerate([10, 16, 24, 30, 42, 50]):
        acc_id = cust_to_accs[cid][0]
        c_dev = [d for d in cust_to_devs[cid] if d[7] == "Trusted"][0]
        loc_id = unusual_loc_ids[idx % len(unusual_loc_ids)]
        amt = round(random.uniform(15000, 48000), 2)
        tx_time = datetime(2026, 9, random.randint(5, 20), random.randint(9, 21), random.randint(1, 59))
        transactions.append((
            tx_id, acc_id, amt, "Payment", "Credit Card",
            tx_time.strftime("%Y-%m-%d %H:%M:%S"),
            loc_id, c_dev[0], "Completed", "International Luxury DutyFree", 0, "LOW"
        ))
        tx_id += 1

    # Step 5e: Scenario 4 - Rapid Transactions Velocity Spike (Rule 4)
    # Rapid bursts: 4 transactions within 8 minutes
    for cid in [6, 15, 28, 38]:
        acc_id = cust_to_accs[cid][0]
        c_dev = [d for d in cust_to_devs[cid] if d[7] == "Trusted"][0]
        c_loc = customers[cid - 1][10]
        burst_start = datetime(2026, 9, random.randint(10, 22), 14, 10, 0)
        for b_idx in range(4):
            b_amt = round(random.uniform(4000, 12000), 2)
            b_time = burst_start + timedelta(minutes=b_idx * 2)
            transactions.append((
                tx_id, acc_id, b_amt, "Payment", "UPI",
                b_time.strftime("%Y-%m-%d %H:%M:%S"),
                c_loc, c_dev[0], "Completed", f"Online Gaming Portal {b_idx+1}", 0, "LOW"
            ))
            tx_id += 1

    # Step 5f: Scenario 5 - Late-Night Transactions (Rule 5)
    # Between 01:00 AM and 03:45 AM
    for cid in [9, 17, 26, 35, 44]:
        acc_id = cust_to_accs[cid][0]
        c_dev = [d for d in cust_to_devs[cid] if d[7] == "Trusted"][0]
        c_loc = customers[cid - 1][10]
        late_amt = round(random.uniform(6000, 22000), 2)
        late_time = datetime(2026, 9, random.randint(12, 24), random.randint(1, 3), random.randint(5, 50))
        transactions.append((
            tx_id, acc_id, late_amt, "Withdrawal", "ATM",
            late_time.strftime("%Y-%m-%d %H:%M:%S"),
            c_loc, c_dev[0], "Completed", "Highway ATM Cash Point", 0, "LOW"
        ))
        tx_id += 1

    # Step 5g: Scenario 6 - Multiple Failed Transactions (Rule 6)
    # 2 Failed attempts followed by a completed or declined attempt within 15 minutes
    for cid in [4, 19, 31, 49]:
        acc_id = cust_to_accs[cid][0]
        c_dev = [d for d in cust_to_devs[cid] if d[7] == "Trusted"][0]
        c_loc = customers[cid - 1][10]
        fail_start = datetime(2026, 9, random.randint(15, 25), 16, 20, 0)
        # Attempt 1: Failed
        transactions.append((
            tx_id, acc_id, 25000.00, "Debit", "Net Banking",
            fail_start.strftime("%Y-%m-%d %H:%M:%S"),
            c_loc, c_dev[0], "Failed", "Merchant Checkout", 0, "LOW"
        ))
        tx_id += 1
        # Attempt 2: Failed
        transactions.append((
            tx_id, acc_id, 25000.00, "Debit", "Net Banking",
            (fail_start + timedelta(minutes=4)).strftime("%Y-%m-%d %H:%M:%S"),
            c_loc, c_dev[0], "Failed", "Merchant Checkout", 0, "LOW"
        ))
        tx_id += 1
        # Attempt 3: Succeeded but suspicious because preceded by 2 failures
        transactions.append((
            tx_id, acc_id, 24500.00, "Debit", "Net Banking",
            (fail_start + timedelta(minutes=9)).strftime("%Y-%m-%d %H:%M:%S"),
            c_loc, c_dev[0], "Completed", "Merchant Checkout", 0, "LOW"
        ))
        tx_id += 1

    # Step 5h: Scenario 7 - Severe Multi-Rule Compound High-Risk Fraud
    # Triggers: HIGH_AMOUNT (+30) + NEW_DEVICE (+20) + UNUSUAL_LOCATION (+20) + LATE_NIGHT (+10) -> Score 80+
    compound_cids = [27, 33, 41, 48, 53]
    for cid in compound_cids:
        acc_id = cust_to_accs[cid][0]
        untrusted_dev = [d for d in cust_to_devs[cid] if d[7] == "Untrusted"][0]
        # foreign or faraway location
        foreign_loc = random.choice([16, 17, 18])  # Dubai, London, Singapore
        heist_amt = round(random.uniform(185000, 490000), 2)
        heist_time = datetime(2026, 9, random.randint(20, 27), random.randint(1, 3), random.randint(10, 45))
        transactions.append((
            tx_id, acc_id, heist_amt, "Transfer", "Wire Transfer",
            heist_time.strftime("%Y-%m-%d %H:%M:%S"),
            foreign_loc, untrusted_dev[0], "Completed", "Global Wire Clearing Ltd", 0, "LOW"
        ))
        tx_id += 1

    # Sort transactions chronologically
    transactions.sort(key=lambda t: t[5])
    # Re-assign sequential transaction_ids after sort
    sorted_transactions = []
    for new_id, t in enumerate(transactions, start=1):
        sorted_transactions.append((
            new_id, t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], t[11]
        ))

    # Format into SQL file
    sql_lines = []
    sql_lines.append("-- ====================================================================")
    sql_lines.append("-- FraudShield: Fraud Transaction Detection & Risk Scoring System")
    sql_lines.append("-- File: 02_sample_data.sql")
    sql_lines.append("-- Description: Realistic seed data with normal and suspicious patterns")
    sql_lines.append("-- Contains: 18 Locations, 60 Customers, 75 Accounts, 100+ Devices, 500+ Transactions")
    sql_lines.append("-- Compatible: MySQL 8.0+ / MySQL Workbench")
    sql_lines.append("-- ====================================================================\n")
    sql_lines.append("USE fraudshield;\n")
    sql_lines.append("SET FOREIGN_KEY_CHECKS = 0;")
    sql_lines.append("TRUNCATE TABLE fraud_audit_log;")
    sql_lines.append("TRUNCATE TABLE fraud_alerts;")
    sql_lines.append("TRUNCATE TABLE transaction_rule_matches;")
    sql_lines.append("TRUNCATE TABLE transactions;")
    sql_lines.append("TRUNCATE TABLE fraud_rules;")
    sql_lines.append("TRUNCATE TABLE devices;")
    sql_lines.append("TRUNCATE TABLE accounts;")
    sql_lines.append("TRUNCATE TABLE locations;")
    sql_lines.append("TRUNCATE TABLE customers;")
    sql_lines.append("SET FOREIGN_KEY_CHECKS = 1;\n")

    # 1. Insert Locations
    sql_lines.append("-- 1. Insert Locations")
    sql_lines.append("INSERT INTO locations (location_id, city, state, country, latitude, longitude) VALUES")
    loc_vals = [f"({i+1}, '{l[0]}', '{l[1]}', '{l[2]}', {l[3]}, {l[4]})" for i, l in enumerate(locations)]
    sql_lines.append(",\n".join(loc_vals) + ";\n")

    # 2. Insert Fraud Rules
    sql_lines.append("-- 2. Insert Configurable Fraud Detection Rules")
    sql_lines.append("INSERT INTO fraud_rules (rule_id, rule_code, rule_name, description, risk_points, active_status) VALUES")
    rules_data = [
        "(1, 'HIGH_AMOUNT', 'Unusually High Amount', 'Transaction amount exceeds 3x customer historical average', 30, TRUE)",
        "(2, 'NEW_DEVICE', 'New or Untrusted Device', 'Transaction executed from newly registered or flagged untrusted device', 20, TRUE)",
        "(3, 'UNUSUAL_LOCATION', 'Unusual Location', 'Transaction executed from a location outside customer historical baseline', 20, TRUE)",
        "(4, 'RAPID_TRANSACTIONS', 'Rapid Transactions (Velocity Spike)', 'Multiple rapid transactions detected on account within 10 minutes', 15, TRUE)",
        "(5, 'LATE_NIGHT_TRANSACTION', 'Late-Night Transaction', 'Transaction initiated during unusual hours (12:00 AM - 4:00 AM)', 10, TRUE)",
        "(6, 'MULTIPLE_FAILED_TRANSACTIONS', 'Multiple Failed Transactions', 'Account experienced 2 or more failed transactions within past 2 hours', 15, TRUE)"
    ]
    sql_lines.append(",\n".join(rules_data) + ";\n")

    # 3. Insert Customers
    sql_lines.append("-- 3. Insert Customers (60 realistic customer profiles)")
    sql_lines.append("INSERT INTO customers (customer_id, full_name, email, phone, date_of_birth, city, state, country, customer_status, created_at) VALUES")
    cust_vals = [f"({c[0]}, '{c[1]}', '{c[2]}', '{c[3]}', '{c[4]}', '{c[5]}', '{c[6]}', '{c[7]}', '{c[8]}', '{c[9]}')" for c in customers]
    sql_lines.append(",\n".join(cust_vals) + ";\n")

    # 4. Insert Accounts
    sql_lines.append("-- 4. Insert Accounts (75 accounts across customers)")
    sql_lines.append("INSERT INTO accounts (account_id, customer_id, account_number, account_type, balance, account_status, opened_date) VALUES")
    acc_vals = [f"({a[0]}, {a[1]}, '{a[2]}', '{a[3]}', {a[4]}, '{a[5]}', '{a[6]}')" for a in accounts]
    sql_lines.append(",\n".join(acc_vals) + ";\n")

    # 5. Insert Devices
    sql_lines.append("-- 5. Insert Devices (110 devices, including trusted and untrusted hardware)")
    sql_lines.append("INSERT INTO devices (device_id, customer_id, device_name, device_type, operating_system, first_used, last_used, trusted_status) VALUES")
    dev_vals = [f"({d[0]}, {d[1]}, '{d[2]}', '{d[3]}', '{d[4]}', '{d[5]}', '{d[6]}', '{d[7]}')" for d in devices]
    sql_lines.append(",\n".join(dev_vals) + ";\n")

    # 6. Insert Transactions
    sql_lines.append(f"-- 6. Insert Transactions ({len(sorted_transactions)} transactions)")
    sql_lines.append("INSERT INTO transactions (transaction_id, account_id, amount, transaction_type, transaction_method, transaction_timestamp, location_id, device_id, transaction_status, merchant_name, risk_score, risk_level) VALUES")
    tx_vals = []
    for t in sorted_transactions:
        dev_str = str(t[7]) if t[7] != "NULL" else "NULL"
        merchant_str = f"'{t[9]}'" if t[9] else "NULL"
        tx_vals.append(f"({t[0]}, {t[1]}, {t[2]}, '{t[3]}', '{t[4]}', '{t[5]}', {t[6]}, {dev_str}, '{t[8]}', {merchant_str}, {t[10]}, '{t[11]}')")
    
    # Chunk inserts into batches of 100 for clean SQL execution
    batch_size = 100
    for b in range(0, len(tx_vals), batch_size):
        chunk = tx_vals[b:b+batch_size]
        if b > 0:
            sql_lines.append("INSERT INTO transactions (transaction_id, account_id, amount, transaction_type, transaction_method, transaction_timestamp, location_id, device_id, transaction_status, merchant_name, risk_score, risk_level) VALUES")
        sql_lines.append(",\n".join(chunk) + ";\n")

    # Note: To analyze transactions, run 04_procedures.sql and CALL analyze_all_transactions();
    sql_lines.append("-- Sample data insertion complete. To analyze all transactions, run 04_procedures.sql and execute CALL analyze_all_transactions();\n")

    with open(r"c:\Users\dasar\.gemini\antigravity\scratch\fraud-detection\database\02_sample_data.sql", "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))

    print(f"Generated 02_sample_data.sql successfully: {len(customers)} customers, {len(accounts)} accounts, {len(devices)} devices, {len(sorted_transactions)} transactions.")

if __name__ == "__main__":
    generate_sql()
