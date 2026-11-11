const WEEK = 7 * 86_400;
/** Start of the ISO week (Monday 00:00 UTC) holding a unix timestamp. 1970-01-01 was a Thursday. */
export const weekStart = (ts: number) => Math.floor((ts - 4 * 86_400) / WEEK) * WEEK + 4 * 86_400;
