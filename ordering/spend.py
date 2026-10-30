"""Hard spend cap.

The ledger counts the *worst-case* fee of everything the tool signs and sends
(base fee + priority fee on the requested CU limit), persists it to disk after
every entry, and refuses anything that would cross the cap.  Because it is
persisted, re-running after a crash continues from the amount already spent
instead of starting a fresh budget.  Lamports parked on sub-payers are not
spending (they are swept back) and are not counted.
"""
import json
import os
import time


class SpendLedger:
    def __init__(self, path, cap_lamports):
        self.path, self.cap = path, int(cap_lamports)
        self.entries = []
        if os.path.exists(path):
            with open(path) as f:
                self.entries = json.load(f).get("entries", [])

    @property
    def spent(self):
        return sum(e["lamports"] for e in self.entries)

    def can_spend(self, lamports):
        return self.spent + lamports <= self.cap

    def add(self, lamports, why):
        if not self.can_spend(lamports):
            raise SystemExit(f"spend cap {self.cap/1e9} SOL would be exceeded by '{why}'")
        self.entries.append({"t": time.time(), "lamports": int(lamports), "why": why})
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"cap_lamports": self.cap, "spent_lamports": self.spent,
                       "entries": self.entries}, f, indent=1)
        os.replace(tmp, self.path)
