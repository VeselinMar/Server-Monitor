import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

export const speedtest = {
  history: (from_dt, to_dt) =>
    api.get("/network/speedtest/history", { params: { from_dt, to_dt } }).then((r) => r.data),
  count: () => api.get("/network/speedtest/count").then((r) => r.data),
  latest: () => api.get("/network/speedtest/latest").then((r) => r.data),
  ingest: () => api.post("/network/speedtest/ingest").then((r) => r.data),
};

export const connectivity = {
  history: (from_dt, to_dt) =>
    api.get("/network/connectivity/history", { params: { from_dt, to_dt } }).then((r) => r.data),
  count: () => api.get("/network/connectivity/count").then((r) => r.data),
  latest: () => api.get("/network/connectivity/latest").then((r) => r.data),
  ingest: () => api.post("/network/connectivity/ingest").then((r) => r.data),
};