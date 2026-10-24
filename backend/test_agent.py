
from app.agent import ask_aria

if __name__ == "__main__":
    question = input("Customer: ")
    answer = ask_aria(question)
    print(f"\nAria: {answer}")
