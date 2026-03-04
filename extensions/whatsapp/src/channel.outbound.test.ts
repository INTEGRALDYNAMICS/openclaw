import { describe, expect, it, vi } from "vitest";
import { whatsappPlugin } from "./channel.js";

describe("whatsapp outbound media", () => {
  it("forwards mediaLocalRoots to sendWhatsApp", async () => {
    const sendWhatsApp = vi.fn().mockResolvedValue({
      messageId: "w1",
      toJid: "1555@s.whatsapp.net",
    });

    const sendMedia = whatsappPlugin.outbound?.sendMedia;
    if (!sendMedia) {
      throw new Error("whatsapp outbound.sendMedia is not configured");
    }

    const result = await sendMedia({
      to: "+1555",
      text: "logo",
      mediaUrl: "/workspace/logo.svg",
      mediaLocalRoots: ["/workspace"],
      deps: { sendWhatsApp },
    });

    expect(sendWhatsApp).toHaveBeenCalledWith(
      "+1555",
      "logo",
      expect.objectContaining({
        verbose: false,
        mediaUrl: "/workspace/logo.svg",
        mediaLocalRoots: ["/workspace"],
      }),
    );
    expect(result).toMatchObject({
      channel: "whatsapp",
      messageId: "w1",
    });
  });
});
