import express, { Request, Response, NextFunction } from "express";
import { randomUUID } from "crypto";
import { InboundEventSchema } from "./validator";
import { logger } from "./logger";

export const app = express();
app.use(express.json());

app.post("/inbound-event", (req: Request, res: Response) => {
  const correlationId = (req.headers["x-correlation-id"] as string) || randomUUID().slice(0, 8);

  logger.info("webhook: received request", { correlationId, ip: req.ip });

  const parsed = InboundEventSchema.safeParse(req.body);

  if (!parsed.success) {
    const errors = parsed.error.flatten();
    logger.warn("webhook: validation failed", { correlationId, errors });
    return res.status(400).json({
      ok: false,
      correlationId,
      errors: parsed.error.flatten(),
    });
  }

  const { type, payload } = parsed.data;
  logger.info("webhook: event accepted", { correlationId, type, id: (payload as { id: string }).id });

  return res.status(202).json({
    ok: true,
    correlationId,
    type,
    message: "Event queued for processing.",
  });
});

app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  logger.error("webhook: unhandled error", { error: err.message });
  res.status(500).json({ ok: false, error: "Internal server error" });
});

if (require.main === module) {
  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => {
    logger.info(`webhook: listening on port ${PORT}`);
  });
}
