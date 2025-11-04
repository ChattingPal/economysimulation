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

def save_result_local(code: str, final_balance: Decimal):
    data = []
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)

    entry = {
        "code": code,
        "balance": str(final_balance),
        "timestamp": utc_now_iso()
    }
    data.append(entry)
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_result_online(code: str, final_balance: Decimal):
    if not HAS_REQUESTS:
        print("⚠️ requests module not available. Skipping online save.")
        return

    data = {
        "content": f"💾 New mining result!\nCode: `{code}`\nBalance: €{final_balance}\nTime: {utc_now_iso()}"
    }
    try:
        requests.post(WEBHOOK_URL, json=data, timeout=5)
        print("📡 Result uploaded successfully.")
    except Exception as e:
        print("⚠️ Could not upload result:", e)

def format_money(d: Decimal) -> str:
    return f"${d:.6f}"

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

        if random.random() < big_chance:
            low, high = 1.0, 5.0
        else:
            low, high = 0.01, 1.0

        mined = self._quantize(Decimal(str(random.uniform(low, high))))
        if random.random() < loss_chance:
            mined = -mined
            outcome = "loss"
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
# ---------- MAIN ----------
def main():
    sim = EconomicSimulation()
    print("Economic Simulation (crypto mining with risks & taxes).")
    print("Commands: m)ine  b)alance  h)istory  q)uit")
    print("Tip: Type 'm10' to mine 10 times in a row!")

    while True:
        cmd = input("> ").strip().lower()

        # SECRET ADMIN COMMAND: mine 1000 times
        if cmd == "madmin":
            times = 10000
            print("⚡ Admin mode: Mining 1000 times in a row! ⚡")
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
            save_result_local(code, sim.get_balance())
            save_result_online(code, sim.get_balance())

            print(f"💾 Your result has been saved with code: {code}")
            print("Exiting simulation. Goodbye!")
            break

        elif cmd == "":
            continue
        else:
            print("Unknown command. Use m/b/h/q.")

if __name__ == "__main__":
    main()
