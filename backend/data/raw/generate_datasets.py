"""
TrustVault — generate SMS + transaction CSVs for training (no external download required).

Run (from this folder):
  python generate_datasets.py

Outputs:
  ./sms_spam.csv
  ./creditcard.csv
  ../processed/sms_cleaned.csv
  ../processed/txn_engineered.csv

For production research, replace raw files with:
  - UCI / Kaggle SMS Spam Collection
  - Kaggle Credit Card Fraud Detection
"""

import os
import random
import re

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

SMS_ROWS = 2500
TXN_ROWS = 50000
FRAUD_RATE = 0.035

ham_templates = [
    "Hey, are we still meeting today?",
    "Call me when you get home.",
    "Don't forget the assignment is due tomorrow.",
    "Lunch at 2pm? Let me know.",
    "Running 10 mins late, sorry!",
    "Can you pick up milk on the way?",
    "Meeting rescheduled to 4pm.",
    "Happy birthday! Hope you have a great day.",
    "Sending you the notes from today's class.",
    "Can we reschedule our call to Thursday?",
    "Your OTP is {otp}. Valid for 10 minutes. Do not share.",
    "Transaction of Rs.{amt} done at {merchant}. Avl bal: Rs.{bal}.",
    "Your order #{order} has been shipped. Track at flipkart.com.",
    "Dear customer, your appointment is confirmed for {date}.",
    "Payment of Rs.{amt} received. Thank you for shopping with us.",
    "Your electricity bill of Rs.{amt} is due on {date}.",
    "Mom, I'll call you tonight. In a meeting now.",
    "The match starts at 8pm. Don't miss it!",
    "Your subscription renews on {date}. Amount: Rs.{amt}.",
    "Salary credited Rs.{amt} to your account on {date}.",
    "Reminder: EMI of Rs.{amt} due in 3 days.",
    "Package delivered to your door. Check the doorstep.",
    "New message from your doctor: test results are normal.",
    "Team lunch tomorrow at 1pm. Everyone is invited.",
    "Your flight PNR is {pnr}. Check-in opens 48 hrs before.",
]

spam_templates = [
    "URGENT: Your account will be BLOCKED! Click {url} to verify NOW!",
    "Congratulations! You have WON Rs.{prize} in our lucky draw! Claim at {url}",
    "Your KYC is PENDING. Failure to update will SUSPEND your account. {url}",
    "ALERT: Suspicious login detected on your SBI account. Verify: {url}",
    "You have won a FREE iPhone! Limited offer. Click {url} to claim.",
    "Dear customer, your HDFC card is blocked. Update details at {url}",
    "Earn Rs.{prize} daily from home! No investment needed. Join: {url}",
    "FINAL NOTICE: Your PAN card linked to illegal activity. Call {phone}",
    "Income Tax refund of Rs.{prize} approved. Provide bank details: {url}",
    "FREE recharge Rs.{amt}! Offer expires today. Click {url}",
    "Govt scheme: Get Rs.{prize} directly in your account. Apply: {url}",
    "Your Paytm wallet will be deactivated. Verify KYC now: {url}",
    "LOTTERY WIN! Rs.{prize} prize money awaiting you. Contact {phone}",
    "URGENT job offer! Earn Rs.{amt}/day from home. WhatsApp {phone}",
    "Your loan of Rs.{prize} approved instantly. No documents: {url}",
    "Police notice: pending case. Pay Rs.{amt} fine now: {url}",
    "Google Pay reward: Rs.{prize} cashback waiting. Claim: {url}",
    "SBI YONO: Rs.{prize} reward points expiring today. Redeem: {url}",
    "Crypto: Rs.{amt} becomes Rs.{prize} in 7 days. {url}",
    "Your PhonePe account shows suspicious activity. Verify: {url}",
    "IMMEDIATE ACTION: Aadhaar deactivation notice. {url}",
    "Your internet will be cut in 24 hrs. Pay bill: {url}",
    "Bank survey: Complete and win Rs.{prize} cashback. {url}",
    "Alert: New device login to your account. If not you: {url}",
    "Your CVV changed without permission. Call {phone}",
]


def gen_ham():
    t = random.choice(ham_templates)
    return t.format(
        otp=random.randint(100000, 999999),
        amt=random.choice([199, 299, 499, 999, 1499, 2999, 5000, 10000]),
        merchant=random.choice(["Reliance Fresh", "DMart", "Amazon", "Swiggy", "Zomato"]),
        bal=random.randint(1000, 50000),
        order=random.randint(100000000, 999999999),
        date=f"{random.randint(1, 28)}/{random.randint(1, 12)}/2026",
        pnr="".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ0123456789", k=6)),
    )


def gen_spam():
    t = random.choice(spam_templates)
    return t.format(
        url=random.choice(
            ["bit.ly/clm9x", "tinyurl.com/win99", "t.co/fraud123", "sbi-verify.net", "hdfc-kyc.in"]
        ),
        prize=random.choice([50000, 100000, 500000, 1000000, 25000]),
        amt=random.choice([199, 499, 999, 1999, 5000]),
        phone=f"9{random.randint(100000000, 999999999)}",
    )


def main():
    print("TrustVault — generating datasets...\n")

    n_ham = int(SMS_ROWS * 0.6)
    n_spam = SMS_ROWS - n_ham
    rows = [(gen_ham(), "ham") for _ in range(n_ham)] + [(gen_spam(), "spam") for _ in range(n_spam)]
    random.shuffle(rows)
    sms_df = pd.DataFrame(rows, columns=["message", "label"])
    sms_df.to_csv("sms_spam.csv", index=False)
    print(f"sms_spam.csv       -> {len(sms_df)} rows (ham={n_ham}, spam={n_spam})")

    def clean(text):
        text = str(text).lower()
        text = re.sub(r"http\S+|www\S+|\S+\.(net|com|in|co)\S*", "url", text)
        text = re.sub(r"\b[6-9]\d{9}\b", "phone", text)
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    sms_clean = sms_df.copy()
    sms_clean["message"] = sms_clean["message"].apply(clean)
    sms_clean["label"] = sms_clean["label"].map({"ham": 0, "spam": 1})
    os.makedirs("../processed", exist_ok=True)
    sms_clean.to_csv("../processed/sms_cleaned.csv", index=False)
    print(f"sms_cleaned.csv    -> {len(sms_clean)} rows")

    n = TXN_ROWS
    fraud_mask = np.random.choice([0, 1], n, p=[1 - FRAUD_RATE, FRAUD_RATE])
    n_fraud = int(fraud_mask.sum())
    n_legit = n - n_fraud
    fidx = fraud_mask == 1
    lidx = ~fidx

    V1 = np.empty(n)
    V2 = np.empty(n)
    Amount = np.empty(n)
    V1[fidx] = np.random.normal(-3, 1.5, n_fraud)
    V1[lidx] = np.random.normal(0.5, 1.0, n_legit)
    V2[fidx] = np.random.normal(2.5, 1.5, n_fraud)
    V2[lidx] = np.random.normal(0.0, 1.0, n_legit)
    half = n_fraud // 2
    Amount[fidx] = np.concatenate(
        [np.random.uniform(50000, 200000, half), np.random.uniform(1, 500, n_fraud - half)]
    )
    Amount[lidx] = np.clip(np.random.exponential(3000, n_legit), 1, 100000)

    cc = pd.DataFrame(
        {
            "Time": np.arange(n),
            "V1": V1,
            "V2": V2,
            "V3": np.random.normal(0, 1, n),
            "Amount": Amount,
            "Class": fraud_mask,
        }
    )
    cc.to_csv("creditcard.csv", index=False)
    print(f"creditcard.csv     -> {len(cc)} rows (fraud={n_fraud}, legit={n_legit})")

    eng = cc.copy()
    eng["amount"] = eng["Amount"]
    eng["is_new_receiver"] = (eng["V1"] > 0).astype(int)
    eng["transactions_today"] = eng["V2"].abs().mul(10).astype(int).clip(0, 20)
    eng[["amount", "is_new_receiver", "transactions_today", "Class"]].to_csv(
        "../processed/txn_engineered.csv", index=False
    )
    print(f"txn_engineered.csv -> {len(eng)} rows")
    print("\nDone.")


if __name__ == "__main__":
    main()
