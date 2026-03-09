import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "/servermonitor"
,
});

export const speedtest = {
  history: (from_dt, to_dt) =>
    api.get("/network/speedtest/history", { params: { from_dt, to_dt } }).then((r) => r.data),
  count: () => api.get("/network/speedtest/count").then((r) => r.data),
  latest: () => api.get("/network/speedtest/latest").then((r) => r.data),
  ingest: () => api.post("/network/speedtest/ingest").then((r) => r.data),
  incidents: (from_dt, to_dt) =>
    api.get("/network/speedtest/incidents", { params: { from_dt, to_dt } }).then((r) => r.data),
};

export const connectivity = {
  history: (from_dt, to_dt) =>
    api.get("/network/connectivity/history", { params: { from_dt, to_dt } }).then((r) => r.data),
  count: () => api.get("/network/connectivity/count").then((r) => r.data),
  latest: () => api.get("/network/connectivity/latest").then((r) => r.data),
  ingest: () => api.post("/network/connectivity/ingest").then((r) => r.data),
};

export const summary = {
  history: (from_date, to_date) =>
    api.get("/network/summary/history", { params: { from_date, to_date } }).then((r) => r.data),
  latest: () => api.get("/network/summary/latest").then((r) => r.data),
};

export const settings = {
  get:  ()     => api.get("/network/settings").then((r) => r.data),
  save: (data) => api.put("/network/settings", data).then((r) => r.data),
};