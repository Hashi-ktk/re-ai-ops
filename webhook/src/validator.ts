import { z } from "zod";

export const EmailPayloadSchema = z.object({
  id: z.string().min(1),
  sender: z.string().email(),
  subject: z.string().min(1),
  body: z.string().min(1),
});

export const DocumentPayloadSchema = z.object({
  id: z.string().min(1),
  filename: z.string().min(1),
  text: z.string().min(1),
});

export const InboundEventSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("email"),    payload: EmailPayloadSchema }),
  z.object({ type: z.literal("document"), payload: DocumentPayloadSchema }),
]);

export type InboundEvent = z.infer<typeof InboundEventSchema>;
export type EmailPayload = z.infer<typeof EmailPayloadSchema>;
export type DocumentPayload = z.infer<typeof DocumentPayloadSchema>;
