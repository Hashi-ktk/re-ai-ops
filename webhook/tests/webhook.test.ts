import request from "supertest";
import { app } from "../src/server";

const VALID_EMAIL_EVENT = {
  type: "email",
  payload: {
    id: "email-001",
    sender: "tenant@example.com",
    subject: "Leaking faucet",
    body: "The kitchen faucet has been dripping for three days.",
  },
};

const VALID_DOCUMENT_EVENT = {
  type: "document",
  payload: {
    id: "doc-001",
    filename: "lease_sample.txt",
    text: "Tenant: Jane Demo. Monthly rent: $1,850. Lease start: 2024-02-01.",
  },
};

describe("POST /inbound-event", () => {
  describe("valid payloads", () => {
    it("accepts a valid email event and returns 202", async () => {
      const res = await request(app).post("/inbound-event").send(VALID_EMAIL_EVENT);
      expect(res.status).toBe(202);
      expect(res.body.ok).toBe(true);
      expect(res.body.type).toBe("email");
      expect(res.body.correlationId).toBeDefined();
    });

    it("accepts a valid document event and returns 202", async () => {
      const res = await request(app).post("/inbound-event").send(VALID_DOCUMENT_EVENT);
      expect(res.status).toBe(202);
      expect(res.body.ok).toBe(true);
      expect(res.body.type).toBe("document");
    });

    it("respects x-correlation-id header", async () => {
      const res = await request(app)
        .post("/inbound-event")
        .set("x-correlation-id", "test-corr-123")
        .send(VALID_EMAIL_EVENT);
      expect(res.body.correlationId).toBe("test-corr-123");
    });
  });

  describe("invalid payloads", () => {
    it("returns 400 for unknown event type", async () => {
      const res = await request(app)
        .post("/inbound-event")
        .send({ type: "fax", payload: {} });
      expect(res.status).toBe(400);
      expect(res.body.ok).toBe(false);
      expect(res.body.errors).toBeDefined();
    });

    it("returns 400 when email sender is not a valid email", async () => {
      const bad = { ...VALID_EMAIL_EVENT, payload: { ...VALID_EMAIL_EVENT.payload, sender: "not-an-email" } };
      const res = await request(app).post("/inbound-event").send(bad);
      expect(res.status).toBe(400);
      expect(res.body.ok).toBe(false);
    });

    it("returns 400 when required fields are missing", async () => {
      const res = await request(app).post("/inbound-event").send({ type: "email", payload: {} });
      expect(res.status).toBe(400);
      expect(res.body.ok).toBe(false);
    });

    it("returns 400 for empty body", async () => {
      const res = await request(app).post("/inbound-event").send({});
      expect(res.status).toBe(400);
    });
  });
});
