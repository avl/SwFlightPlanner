from selenium import selenium

def create_sel():
    return selenium("localhost", 4444, "*firefox", "http://localhost:5000/")

