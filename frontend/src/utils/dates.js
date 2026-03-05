import { subHours, format, parseISO } from "date-fns";

export const PRESETS = [
  { label: "24h", hours: 24 },
  { label: "7d", hours: 24 * 7 },
  { label: "30d", hours: 24 * 30 },
];

export function presetRange(hours) {
  const to = new Date();
  const from = subHours(to, hours);
  return { from, to };
}

export function toISO(date) {
  return format(date, "yyyy-MM-dd'T'HH:mm:ss");
}

export function fmtTimestamp(ts) {
  return format(parseISO(ts), "MMM d, HH:mm");
}

export function fmtDate(ts) {
  return format(parseISO(ts), "MMM d");
}