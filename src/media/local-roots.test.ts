import path from "node:path";
import { describe, expect, it } from "vitest";
import type { OpenClawConfig } from "../config/config.js";
import { withEnv } from "../test-utils/env.js";
import { getAgentScopedMediaLocalRoots } from "./local-roots.js";

describe("agent scoped media local roots", () => {
  it("includes the default agent workspace when agentId is omitted", () => {
    withEnv({ OPENCLAW_STATE_DIR: "/tmp/openclaw-state-media-roots-default" }, () => {
      const cfg = {
        agents: {
          list: [
            {
              id: "main",
              default: true,
              workspace: "/home/ubuntu/projects/IntegralDynamicsProjectFinal",
            },
          ],
        },
      } as OpenClawConfig;

      const roots = getAgentScopedMediaLocalRoots(cfg);

      expect(roots).toContain(path.resolve("/home/ubuntu/projects/IntegralDynamicsProjectFinal"));
      expect(roots).toContain(path.resolve("/tmp/openclaw-state-media-roots-default/media"));
    });
  });

  it("includes the explicit agent workspace when agentId is provided", () => {
    withEnv({ OPENCLAW_STATE_DIR: "/tmp/openclaw-state-media-roots-explicit" }, () => {
      const cfg = {
        agents: {
          list: [
            { id: "main", default: true, workspace: "/workspace/default" },
            { id: "growth", workspace: "/workspace/growth" },
          ],
        },
      } as OpenClawConfig;

      const roots = getAgentScopedMediaLocalRoots(cfg, "growth");

      expect(roots).toContain(path.resolve("/workspace/growth"));
      expect(roots).not.toContain(path.resolve("/workspace/default"));
      expect(roots).toContain(path.resolve("/tmp/openclaw-state-media-roots-explicit/media"));
    });
  });
});
