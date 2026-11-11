/**
 * `transact` data (wincode, little-endian) after the 1-byte tag:
 * expiry_unix_ts u64 (8) | tx_viewing_pk [u8;33] | salt [u8;16] |
 * interface_transfers: u8 count, then per leg a u8 variant + u64 amount (+ u8 bump for SPL).
 * Variants: 0 SolDeposit, 1 SolWithdrawal, 2 SplDeposit, 3 SplWithdrawal.
 * We read only the leg directions, never the amounts.
 */
export const interfaceLegs = (data: Uint8Array) => {
  let offset = 1 + 8 + 33 + 16;
  const count = data[offset++] ?? 0;
  let deposits = 0;
  let withdrawals = 0;
  for (let i = 0; i < count; i++) {
    const variant = data[offset];
    if (variant === undefined || variant > 3) throw new Error(`unknown interface transfer variant ${variant}`);
    if (variant === 0 || variant === 2) deposits++;
    else withdrawals++;
    offset += 1 + 8 + (variant >= 2 ? 1 : 0);
  }
  return { deposits, withdrawals };
};
