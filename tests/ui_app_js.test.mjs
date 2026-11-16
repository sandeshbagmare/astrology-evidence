import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import test from "node:test";

test("profile submission sends the selected daylight-saving occurrence", async () => {
  const handlers = {};
  const values = {
    csrf_token: "form-token",
    alias: "Synthetic profile",
    birth_date: "2024-11-03",
    local_time: "01:30",
    time_precision: "exact",
    latitude: "40.7",
    longitude: "-74.0",
    timezone: "America/New_York",
    timezone_history: "confirmed",
    fold: "1",
    storage_consent: "true",
    notice_version: "privacy-1",
  };
  const form = {
    dataset: { api: "/api/profiles", success: "/dashboard" },
    addEventListener(name, callback) {
      handlers[name] = callback;
    },
    querySelector(selector) {
      return selector === "[role=alert]" ? { textContent: "" } : null;
    },
  };
  const document = {
    documentElement: { dataset: { csrfCookie: "ae_csrf" } },
    cookie: "ae_csrf=cookie-token",
    querySelectorAll(selector) {
      return selector === "form[data-api]" ? [form] : [];
    },
    querySelector() {
      return null;
    },
  };
  const requests = [];
  const context = {
    document,
    location: { origin: "http://testserver", href: "" },
    FormData: class {
      constructor() {}
      [Symbol.iterator]() {
        return Object.entries(values)[Symbol.iterator]();
      }
    },
    fetch: async (url, options) => {
      requests.push({ url, options });
      return { ok: true, json: async () => ({ id: "profile-id" }) };
    },
    setInterval,
    clearInterval,
  };
  runInNewContext(
    readFileSync("src/astrology_evidence/web/static/app.js", "utf8"),
    context,
  );

  await handlers.submit({ preventDefault() {} });

  const submitted = JSON.parse(requests[0].options.body);
  assert.equal(submitted.birth_input.fold, 1);
  assert.equal(requests[0].url, "/api/profiles");
});

test("profile submission stops before saving an ambiguous time without an occurrence", async () => {
  let submit;
  const alert = { textContent: "" };
  const values = {
    alias: "Synthetic profile",
    birth_date: "2024-11-03",
    local_time: "01:30",
    time_precision: "exact",
    latitude: "40.7",
    longitude: "-74.0",
    timezone: "America/New_York",
    timezone_history: "confirmed",
    fold: "",
    storage_consent: "true",
    notice_version: "privacy-1",
  };
  const form = {
    dataset: { api: "/api/profiles", success: "/dashboard" },
    addEventListener(name, callback) {
      if (name === "submit") submit = callback;
    },
    querySelector() {
      return alert;
    },
  };
  const document = {
    documentElement: { dataset: { csrfCookie: "ae_csrf" } },
    cookie: "ae_csrf=cookie-token",
    querySelectorAll(selector) {
      return selector === "form[data-api]" ? [form] : [];
    },
    querySelector() {
      return null;
    },
  };
  const requests = [];
  runInNewContext(readFileSync("src/astrology_evidence/web/static/app.js", "utf8"), {
    document,
    location: { origin: "http://testserver", href: "" },
    FormData: class {
      [Symbol.iterator]() {
        return Object.entries(values)[Symbol.iterator]();
      }
    },
    fetch: async (url, options) => {
      requests.push({ url, options });
      return {
        ok: true,
        json: async () => ({
          ambiguous: true,
          candidates: [
            { fold: 0, label: "First occurrence (UTC-04:00)" },
            { fold: 1, label: "Second occurrence (UTC-05:00)" },
          ],
        }),
      };
    },
  });

  await submit({ preventDefault() {} });

  assert.deepEqual(requests.map(request => request.url), ["/api/time-options"]);
  assert.match(alert.textContent, /Choose the first or second occurrence/);
});

test("prefilled edits resolve offsets once and changed inputs clear the old choice", async () => {
  const changeHandlers = {};
  const controls = {
    birth_date: { value: "2024-11-03" },
    local_time: { value: "01:30" },
    timezone: { value: "America/New_York" },
    time_precision: { value: "exact" },
    profile_id: { value: "synthetic-profile" },
  };
  for (const [name, control] of Object.entries(controls)) {
    control.addEventListener = (event, callback) => {
      changeHandlers[name] = callback;
    };
  }
  const fold = {
    value: "1",
    required: false,
    options: [],
    replaceChildren(...options) {
      this.options = options;
      this.value = options[0]?.value || "";
    },
    add(option) {
      this.options.push(option);
    },
  };
  const status = { textContent: "" };
  const form = {
    elements: {
      namedItem(name) {
        return name === "fold" ? fold : controls[name];
      },
    },
    querySelector() {
      return status;
    },
  };
  const replies = [
    {
      ambiguous: true,
      candidates: [
        { fold: 0, offset: "UTC-04:00", label: "First occurrence (UTC-04:00)" },
        { fold: 1, offset: "UTC-05:00", label: "Second occurrence (UTC-05:00)" },
      ],
    },
    {
      ambiguous: false,
      candidates: [{ fold: 0, offset: "UTC-05:00", label: "First occurrence (UTC-05:00)" }],
    },
  ];
  let calls = 0;
  runInNewContext(readFileSync("src/astrology_evidence/web/static/app.js", "utf8"), {
    document: {
      documentElement: { dataset: { csrfCookie: "ae_csrf" } },
      cookie: "ae_csrf=cookie-token",
      querySelectorAll(selector) {
        return selector === "[data-profile-form]" ? [form] : [];
      },
      querySelector() {
        return null;
      },
    },
    Option: class {
      constructor(text, value) {
        this.text = text;
        this.value = value;
      }
    },
    location: { origin: "http://testserver" },
    fetch: async () => {
      const reply = replies[calls++];
      return { ok: true, json: async () => reply };
    },
  });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(calls, 1);
  assert.equal(fold.value, "1");
  assert.equal(fold.options[1].text, "First occurrence (UTC-04:00)");
  assert.equal(fold.options[2].text, "Second occurrence (UTC-05:00)");

  controls.birth_date.value = "2024-11-04";
  await changeHandlers.birth_date({ type: "change" });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(calls, 2);
  assert.equal(fold.value, "");
  assert.equal(fold.required, false);
  assert.equal(fold.options.length, 1);
  assert.equal(fold.options[0].text, "UTC-05:00 (only valid occurrence)");
});

test("old delayed offset JSON cannot repopulate a changed time", async () => {
  const handlers = {};
  const controls = {
    birth_date: { value: "2024-11-03" },
    local_time: { value: "01:30" },
    timezone: { value: "America/New_York" },
    time_precision: { value: "exact" },
    profile_id: { value: "synthetic-profile" },
  };
  for (const [name, control] of Object.entries(controls)) {
    control.addEventListener = (event, callback) => { handlers[name] = callback; };
  }
  const fold = {
    value: "1", required: false, options: [],
    replaceChildren(...options) { this.options = options; this.value = options[0]?.value || ""; },
    add(option) { this.options.push(option); },
  };
  const status = { textContent: "" };
  const form = {
    elements: { namedItem: name => name === "fold" ? fold : controls[name] },
    querySelector: () => status,
  };
  let releaseOldJson;
  const oldJson = new Promise(resolve => { releaseOldJson = resolve; });
  let calls = 0;
  runInNewContext(readFileSync("src/astrology_evidence/web/static/app.js", "utf8"), {
    document: {
      documentElement: { dataset: { csrfCookie: "ae_csrf" } },
      cookie: "ae_csrf=cookie-token",
      querySelectorAll: selector => selector === "[data-profile-form]" ? [form] : [],
      querySelector: () => null,
    },
    Option: class {
      constructor(text, value) { this.text = text; this.value = value; }
    },
    location: { origin: "http://testserver" },
    fetch: async () => {
      if (calls++ === 0) return { ok: true, json: () => oldJson };
      return { ok: true, json: async () => ({
        ambiguous: false,
        candidates: [{ fold: 0, offset: "UTC-05:00" }],
      }) };
    },
  });
  await new Promise(resolve => setImmediate(resolve));
  controls.birth_date.value = "2024-11-04";
  handlers.birth_date({ type: "change" });
  await new Promise(resolve => setImmediate(resolve));
  releaseOldJson({
    ambiguous: true,
    candidates: [
      { fold: 0, offset: "UTC-04:00", label: "First occurrence (UTC-04:00)" },
      { fold: 1, offset: "UTC-05:00", label: "Second occurrence (UTC-05:00)" },
    ],
  });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(fold.value, "");
  assert.equal(fold.required, false);
  assert.equal(fold.options.length, 1);
  assert.equal(fold.options[0].text, "UTC-05:00 (only valid occurrence)");
});
