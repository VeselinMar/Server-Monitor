import { subHours, format, parseISO } from "date-fns";

export const PRESETS = [
  { label: "24h", hours: 24 },
  { label: "7d", hours: 24 * 7 },
];

export function presetRange(hours) {
  const to = new Date();
  const from = subHours(to, hours);
  return { from, to };
}

export function toISO(date) {
  return date.toISOString();
}

function parseUTCTimestamp(ts) {
  const normalized = ts.endsWith("Z") ? ts : `${ts}Z`;
  return parseISO(normalized);
}

export function fmtTimestamp(ts) {
  return format(parseUTCTimestamp(ts), "MMM d, HH:mm");
}

export function fmtDate(ts) {
  return format(parseUTCTimestamp(ts), "MMM d");
}
