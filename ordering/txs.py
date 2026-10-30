"""Transaction construction.

Every probe transaction is the same shape so that only the variables we
control differ:
    [ComputeBudget.SetComputeUnitLimit(cu_limit),
     ComputeBudget.SetComputeUnitPrice(cu_price),
     Memo("ord|<run>|<batch>|<idx>")]
The only writable account is the fee payer.  Using one payer per transaction
makes the probes mutually independent (no lock conflicts); reusing one payer
for a group forces a write-lock conflict between them.
"""
import base64
import json
import os

from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.hash import Hash
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction

MEMO_PROGRAM = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
BASE_FEE_PER_SIG = 5000  # lamports


def load_keypair(path):
    with open(path) as f:
        return Keypair.from_bytes(bytes(json.load(f)))


def save_keypair(kp, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(list(bytes(kp)), f)
    os.chmod(path, 0o600)


def memo_ix(text: str) -> Instruction:
    return Instruction(MEMO_PROGRAM, text.encode(), [])


def probe_tx(payer: Keypair, blockhash: Hash, cu_limit: int, cu_price: int, memo: str):
    ixs = [set_compute_unit_limit(cu_limit), set_compute_unit_price(cu_price), memo_ix(memo)]
    msg = Message.new_with_blockhash(ixs, payer.pubkey(), blockhash)
    return Transaction([payer], msg, blockhash)


def transfer_tx(payer: Keypair, transfers, blockhash: Hash, extra_signers=()):
    ixs = [transfer(TransferParams(from_pubkey=src, to_pubkey=dst, lamports=lam))
           for src, dst, lam in transfers]
    msg = Message.new_with_blockhash(ixs, payer.pubkey(), blockhash)
    return Transaction([payer, *extra_signers], msg, blockhash)


def max_fee(cu_limit: int, cu_price: int, sigs: int = 1) -> int:
    """Upper bound of what a probe can cost (priority fee is charged on the
    requested limit, rounded up)."""
    return sigs * BASE_FEE_PER_SIG + -(-cu_limit * cu_price // 1_000_000)


def b64(tx) -> str:
    return base64.b64encode(bytes(tx)).decode()
