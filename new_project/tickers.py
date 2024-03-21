import yfinance as yf
import matplotlib.pyplot as plt

apple = yf.Ticker("APPL")
print(apple.info)
