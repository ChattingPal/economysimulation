import random
import datetime
from decimal import Decimal, getcontext
import secrets
import json
import os

# Optional requests import for online saving
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ---------- CONFIG ----------
SAVE_FILE = "results.json"
WEBHOOK_URL = "https://discord.com/api/webhooks/1435343930282475712/FVWIRyxnkMpBo5PZm4Qr6DXfycIG_eUohKE1jvfgwFnH18ps4cG7dTO5mRruJ4giooUr"
PRECISION = Decimal('0.000001')  # smallest unit displayed
getcontext().prec = 28

# ---------- HELPERS ----------
def generate_code(length=12):
    return ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789') for _ in range(length))

def utc_now_iso():
    """Return timezone-aware UTC timestamp as ISO string."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def save_result_local(code: str, final_balance: Decimal, discord_username: str):
    data = []
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)

    entry = {
        "code": code,
        "balance": str(final_balance),
        "discord_user": discord_username,  # Save the Discord username
        "timestamp": utc_now_iso()
    }
    data.append(entry)
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_result_online(code: str, final_balance: Decimal, discord_username: str):
    if not HAS_REQUESTS:
        print("⚠️ requests module not available. Skipping online save.")
        return

    data = {
        "content": f"💾 New mining result!\nCode: `{code}`\nBalance: €{final_balance}\nDiscord User: {discord_username}\nTime: {utc_now_iso()}"
    }
    try:
        requests.post(WEBHOOK_URL, json=data, timeout=5)
        print("📡 Result uploaded successfully.")
    except Exception as e:
        print("⚠️ Could not upload result:", e)

def format_money(d: Decimal) -> str:
    return f"€{d:.6f}"

# ---------- SIMULATION ----------
class EconomicSimulation:
    def __init__(self, starting_balance: Decimal = Decimal('0.0')):
        self.balance = starting_balance
        self.ledger = []

    def _quantize(self, value: Decimal) -> Decimal:
        return value.quantize(PRECISION)

    def mine(self) -> tuple[Decimal, str]:
        big_chance = 0.05
        loss_chance = 0.15
        big_loss_chance = 0.035  # 0.35% chance for a big loss
        extreme_loss_chance = 0.0005  # 0.05% chance for a 125% loss
        max_loss = Decimal('30')  # Maximum loss cap per mine operation (adjustable)

        if random.random() < big_chance:
            low, high = 1.0, 5.0
        else:
            low, high = 0.01, 1.0

        mined = self._quantize(Decimal(str(random.uniform(low, high))));

        if random.random() < loss_chance:
            # Loss occurs, but with a chance to be a bigger loss
            if random.random() < extreme_loss_chance:
                # 125% loss of current balance
                mined = -self._quantize(self.balance * Decimal('1.25'))
                outcome = "extreme loss"
            elif random.random() < big_loss_chance:
                # Reduced big loss to 30% of balance instead of 50%
                mined = -self._quantize(self.balance * Decimal('0.15'))
                outcome = "big loss"
            else:
                mined = -mined
                outcome = "loss"

            # Ensure that losses do not exceed the maximum loss cap
            if abs(mined) > max_loss:
                mined = -max_loss
                outcome = "loss cap"

        else:
            outcome = "mine"

        self.balance = self._quantize(self.balance + mined)
        self.ledger.append((utc_now_iso(), outcome, mined, self.balance))
        return mined, outcome

    def get_balance(self) -> Decimal:
        return self._quantize(self.balance)

    def history(self, limit: int = 50):
        return list(self.ledger[-limit:])

    def apply_exit_tax(self, rate: Decimal = Decimal("0.40")) -> Decimal:
        tax = self._quantize(self.balance * rate)
        self.balance = self._quantize(self.balance - tax)
        self.ledger.append((utc_now_iso(), "tax", -tax, self.balance))
        return tax

# ---------- MAIN ----------
def main():
    print("EconomySimulation™ by AllGameWizard")
    print("Copyright © 2025 AllGameWizard - CC BY-NC 4.0 - All rights reserved.")
    print("Commands: m)ine  b)alance  h)istory  q)uit")
    print("Tip: Type 'm10' to mine 10 times in a row!")

    # Prompt for Discord username
    discord_username = input("Please enter your Discord username (e.g., @username): ").strip()

    # Validate the username format (basic check)
    if not discord_username.startswith("@") or len(discord_username) < 3:
        print("⚠️ Invalid Discord username format. Please use '@username'. Exiting.")
        return  # Exit if the username is invalid

    # Now start the simulation
    sim = EconomicSimulation()

    while True:
        cmd = input("> ").strip().lower()

        # SECRET ADMIN COMMAND: mine 1000 times
        if cmd == "madmin":
            times = 10000
            print("⚡ Admin mode: Mining 10000 times in a row! ⚡")
        elif cmd.startswith("m"):
            times = int(''.join(filter(str.isdigit, cmd)) or 1)
        else:
            times = 0

        if times > 0:
            total_mined = Decimal('0')
            total_lost = Decimal('0')

            for _ in range(times):
                mined, outcome = sim.mine()
                if mined >= 0:
                    total_mined += mined
                else:
                    total_lost += -mined

            if times > 1:
                print(f"Mined {times} times:")
                print(f"  ⛏️  Total mined: {format_money(total_mined)}")
                print(f"  ⚠️  Total lost: {format_money(total_lost)}")
                print(f"  💰 New balance: {format_money(sim.get_balance())}")
            else:
                if mined >= 0:
                    print(f"Mined {format_money(mined)} — New balance: {format_money(sim.get_balance())}")
                else:
                    print(f"⚠️  You lost {format_money(-mined)} — New balance: {format_money(sim.get_balance())}")
            continue

        elif cmd in ("b", "balance"):
            print(f"Balance: {format_money(sim.get_balance())}")

        elif cmd in ("h", "history"):
            hist = sim.history()
            if not hist:
                print("No transactions yet.")
            else:
                for ts, action, amount, bal in hist:
                    sign = "-" if amount < 0 else "+"
                    print(f"{ts} | {action:<5} | {sign}{format_money(abs(amount)):>11} -> {format_money(bal)}")

        elif cmd in ("q", "quit", "exit"):
            balance_before = sim.get_balance()
            tax_paid = sim.apply_exit_tax()
            print(f"\n💰 Balance before tax: {format_money(balance_before)}")
            print(f"🏛️  Government took 40%: {format_money(tax_paid)}")
            print(f"💸 Final balance after tax: {format_money(sim.get_balance())}")

            # Save results
            code = generate_code()
            save_result_local(code, sim.get_balance(), discord_username)
            save_result_online(code, sim.get_balance(), discord_username)

            print(f"💾 Your result has been saved with code: {code}")
            print("Exiting simulation. Goodbye!")
            break

        elif cmd == "":
            continue
        else:
            print("Unknown command. Use m/b/h/q.")

if __name__ == "__main__":
    main()
