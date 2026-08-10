import smtplib, ssl

with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
    server.ehlo()
    server.starttls(context=ssl.create_default_context())
    server.ehlo()
    server.login("aegulasandeep@gmail.com", "zvyq fvhd ctcw rxte")
    print("Login successful!")