import sys
from colorama import Fore, Style
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
import pyfiglet
import json

console = Console()

# Load data from JSON files
def load_data(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        console.print(f"[red]Error: {filename} not found.[/]")
        return {}
    except json.JSONDecodeError:
        console.print(f"[red]Error: Failed to decode {filename}. Ensure it is valid JSON.[/]")
        return {}

def save_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

products = load_data("products.json")
coupons = load_data("coupons.json")
cards = load_data("cards.json")

cart = {}

def retry_operation(operation):
    for attempt in range(3):
        result = operation()
        if result is not None:
            return result
        console.print(f"[red]Attempt {attempt + 1} failed. {2 - attempt} attempts remaining.[/]")
    console.print("[bold red]Maximum attempts reached. Starting over.[/]")
    return None

def display_products():
    table = Table(title="Available Products")
    table.add_column("Code", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Price", style="yellow")
    table.add_column("Stock", style="magenta")

    for code, details in products.items():
        table.add_row(code, details['name'], str(details['price']), str(details['stock']))
    console.print(table)

def add_to_cart():
    def inner_add_to_cart():
        display_products()
        code = input(Fore.CYAN + "\nEnter the product code to purchase: " + Style.RESET_ALL).strip().upper()

        if code not in products:
            console.print("[red]Invalid product code. Try again.[/]")
            return None

        if products[code]["stock"] <= 0:
            console.print("[red]Sorry, this product is out of stock.[/]")
            return None

        try:
            quantity = int(input(f"Enter quantity for {products[code]['name']}: ").strip())
        except ValueError:
            console.print("[red]Invalid quantity. Enter a number.[/]")
            return None

        if quantity > products[code]["stock"]:
            console.print(f"[red]Only {products[code]['stock']} units are available.[/]")
            return None

        confirm = input(f"Confirm adding {quantity} x {products[code]['name']} to cart? (y/n): ").strip().lower()

        if confirm == "y":
            if code in cart:
                cart[code] += quantity
            else:
                cart[code] = quantity
            products[code]["stock"] -= quantity
            save_data("products.json", products)
            console.print(f"[green]{quantity} x {products[code]['name']} added to cart.[/]")
            return True

        console.print("[yellow]Action cancelled.[/]")
        return None

    while True:
        if retry_operation(inner_add_to_cart):
            another = input(Fore.CYAN + "Do you want to add more products? (y/n): " + Style.RESET_ALL).strip().lower()
            if another != "y":
                break

def calculate_total():
    total = 0
    table = Table(title="Your Cart")
    table.add_column("Name", style="green")
    table.add_column("Quantity", style="yellow")
    table.add_column("Price", style="magenta")
    table.add_column("Total", style="cyan")

    for code, quantity in cart.items():
        cost = quantity * products[code]["price"]
        total += cost
        table.add_row(products[code]['name'], str(quantity), str(products[code]['price']), str(cost))
    console.print(table)
    console.print(f"[bold yellow]Total: {total}[/]")
    return total

def apply_coupon(total):
    def inner_apply_coupon():
        code = input(Fore.CYAN + "Enter coupon code (if any, type 'n' if none): " + Style.RESET_ALL).strip()
        if code.lower() == 'n':
            console.print("[yellow]No coupon applied.[/]")
            return total
        if code in coupons:
            discount = total * (coupons[code] / 100)
            new_total = total - discount
            console.print(f"[green]Coupon applied! Discount: {discount:.2f}[/]")
            return new_total
        console.print("[red]Invalid coupon code.[/]")
        return None

    new_total = retry_operation(inner_apply_coupon)
    return new_total if new_total is not None else total

def pay_with_cash(total):
    def inner_pay_with_cash():
        try:
            cash = float(input(Fore.CYAN + f"Total amount: {total}. Insert cash: " + Style.RESET_ALL).strip())
            if cash < total:
                console.print("[red]Insufficient amount. Try again.[/]")
                return None
            elif cash > total:
                console.print(f"[green]Transaction successful! Change returned: {cash - total:.2f}[/]")
            else:
                console.print("[green]Transaction successful! Thank you.[/]")
            return True
        except ValueError:
            console.print("[red]Invalid amount. Try again.[/]")
            return None

    retry_operation(inner_pay_with_cash)

def pay_with_card(total):
    def inner_pay_with_card():
        card_number = input(Fore.CYAN + "Enter card number: " + Style.RESET_ALL).strip()
        if card_number not in cards:
            console.print("[red]Invalid card number.[/]")
            return None

        pin = input(Fore.CYAN + "Enter PIN: " + Style.RESET_ALL).strip()
        if cards[card_number]["pin"] != pin:
            console.print("[red]Invalid PIN.[/]")
            return None

        if cards[card_number]["balance"] < total:
            console.print("[red]Insufficient balance.[/]")
            return None

        cards[card_number]["balance"] -= total
        save_data("cards.json", cards)
        console.print("[green]Transaction successful! Thank you.[/]")
        return True

    retry_operation(inner_pay_with_card)

def billing():
    total = calculate_total()
    total = apply_coupon(total)

    console.print("\n[bold cyan]Payment Options:[/]")
    console.print("1. Cash")
    console.print("2. Card")
    
    def inner_billing():
        option = input(Fore.CYAN + "Choose payment option (1/2): " + Style.RESET_ALL).strip()
        if option == "1":
            pay_with_cash(total)
            return True
        elif option == "2":
            pay_with_card(total)
            return True
        console.print("[red]Invalid option. Try again.[/]")
        return None

    retry_operation(inner_billing)

# Main flow
banner = pyfiglet.figlet_format("Vending Machine")
console.print(f"[bold magenta]{banner}[/]")

while True:
    console.print("[bold cyan]Welcome to the Ultimate Vending Machine![/]")

    add_to_cart()

    if cart:
        billing()
        break
    else:
        console.print("[red]Cart is empty. Starting over.[/]")

console.print("\n[bold green]Thank you for using the vending machine! Goodbye.[/]")
